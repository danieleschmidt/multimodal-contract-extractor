#!/bin/bash
# Advanced Release Automation Script
# Semantic versioning, automated changelog, and comprehensive release pipeline

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
RELEASE_BRANCH_PREFIX="${RELEASE_BRANCH_PREFIX:-release/}"
VERSION_FILE="${VERSION_FILE:-pyproject.toml}"
CHANGELOG_FILE="${CHANGELOG_FILE:-CHANGELOG.md}"
PYTHON_CMD="${PYTHON_CMD:-python}"

# Release configuration
DRY_RUN="${DRY_RUN:-false}"
SKIP_TESTS="${SKIP_TESTS:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"
SKIP_DOCKER="${SKIP_DOCKER:-false}"
AUTO_MERGE="${AUTO_MERGE:-false}"

echo -e "${BLUE}=== Advanced Release Automation ===${NC}"
echo -e "Current branch: ${CURRENT_BRANCH}"
echo -e "Default branch: ${DEFAULT_BRANCH}"
echo -e "Version file: ${VERSION_FILE}"
echo -e "Dry run: ${DRY_RUN}"
echo ""

# Function to check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}Error: Not in a git repository${NC}"
        exit 1
    fi
}

# Function to check for uncommitted changes
check_clean_working_tree() {
    if ! git diff-index --quiet HEAD --; then
        echo -e "${RED}Error: Working tree has uncommitted changes${NC}"
        echo "Please commit or stash your changes before proceeding."
        exit 1
    fi
}

# Function to check if branch is up to date with remote
check_branch_sync() {
    local branch="$1"
    
    echo -e "${YELLOW}Checking if branch is synced with remote...${NC}"
    
    # Fetch latest changes
    git fetch origin
    
    local local_commit=$(git rev-parse "$branch")
    local remote_commit=$(git rev-parse "origin/$branch" 2>/dev/null || echo "")
    
    if [[ -n "$remote_commit" ]] && [[ "$local_commit" != "$remote_commit" ]]; then
        echo -e "${RED}Error: Branch $branch is not synced with remote${NC}"
        echo "Please pull the latest changes: git pull origin $branch"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Branch is synced with remote${NC}"
}

# Function to get current version from file
get_current_version() {
    if [[ -f "$VERSION_FILE" ]]; then
        if [[ "$VERSION_FILE" == "pyproject.toml" ]]; then
            grep '^version = ' "$VERSION_FILE" | sed 's/version = "\(.*\)"/\1/' | tr -d '"'
        elif [[ "$VERSION_FILE" == "package.json" ]]; then
            grep '"version"' "$VERSION_FILE" | sed 's/.*"version": "\(.*\)".*/\1/'
        else
            # Try to find version in other formats
            grep -E '(version|VERSION)' "$VERSION_FILE" | head -1 | sed 's/.*[=:] *["\047]\?\([0-9][^"]*\)["\047]\?.*/\1/'
        fi
    else
        echo "0.0.0"
    fi
}

# Function to parse semantic version
parse_version() {
    local version="$1"
    
    if [[ ! "$version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$ ]]; then
        echo -e "${RED}Error: Invalid semantic version format: $version${NC}"
        exit 1
    fi
    
    MAJOR=${BASH_REMATCH[1]}
    MINOR=${BASH_REMATCH[2]}
    PATCH=${BASH_REMATCH[3]}
    PRERELEASE=${BASH_REMATCH[4]}
    BUILD=${BASH_REMATCH[5]}
}

# Function to increment version
increment_version() {
    local current_version="$1"
    local increment_type="$2"
    
    parse_version "$current_version"
    
    case "$increment_type" in
        "major")
            MAJOR=$((MAJOR + 1))
            MINOR=0
            PATCH=0
            ;;
        "minor")
            MINOR=$((MINOR + 1))
            PATCH=0
            ;;
        "patch")
            PATCH=$((PATCH + 1))
            ;;
        *)
            echo -e "${RED}Error: Invalid increment type: $increment_type${NC}"
            echo "Valid types: major, minor, patch"
            exit 1
            ;;
    esac
    
    echo "${MAJOR}.${MINOR}.${PATCH}"
}

# Function to detect version increment type from commits
detect_version_increment() {
    local since_tag="$1"
    
    echo -e "${YELLOW}Analyzing commits since $since_tag...${NC}"
    
    # Get commit messages since last tag
    local commit_messages
    if [[ -n "$since_tag" ]]; then
        commit_messages=$(git log --pretty=format:"%s" "$since_tag..HEAD")
    else
        commit_messages=$(git log --pretty=format:"%s")
    fi
    
    # Analyze commit messages for conventional commit patterns
    local has_breaking=false
    local has_feature=false
    local has_fix=false
    
    while IFS= read -r message; do
        if [[ "$message" =~ ^[a-z]+(\(.+\))?!: ]] || [[ "$message" =~ BREAKING\ CHANGE ]]; then
            has_breaking=true
        elif [[ "$message" =~ ^feat(\(.+\))?: ]]; then
            has_feature=true
        elif [[ "$message" =~ ^fix(\(.+\))?: ]]; then
            has_fix=true
        fi
    done <<< "$commit_messages"
    
    # Determine increment type
    if [[ "$has_breaking" == true ]]; then
        echo "major"
    elif [[ "$has_feature" == true ]]; then
        echo "minor"
    elif [[ "$has_fix" == true ]]; then
        echo "patch"
    else
        echo "patch"  # Default to patch for other changes
    fi
}

# Function to update version in file
update_version_file() {
    local new_version="$1"
    
    echo -e "${YELLOW}Updating version in $VERSION_FILE to $new_version...${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN] Would update version to $new_version${NC}"
        return
    fi
    
    if [[ "$VERSION_FILE" == "pyproject.toml" ]]; then
        sed -i "s/^version = .*/version = \"$new_version\"/" "$VERSION_FILE"
    elif [[ "$VERSION_FILE" == "package.json" ]]; then
        sed -i "s/\"version\": \".*\"/\"version\": \"$new_version\"/" "$VERSION_FILE"
    else
        # Generic version update
        sed -i "s/version.*=.*/version = \"$new_version\"/" "$VERSION_FILE"
    fi
    
    echo -e "${GREEN}✓ Version updated to $new_version${NC}"
}

# Function to generate changelog
generate_changelog() {
    local version="$1"
    local since_tag="$2"
    
    echo -e "${YELLOW}Generating changelog for version $version...${NC}"
    
    local changelog_entry=""
    local temp_changelog=$(mktemp)
    
    # Create changelog header
    cat > "$temp_changelog" << EOF
## [$version] - $(date +%Y-%m-%d)

EOF
    
    # Get commits since last tag
    if [[ -n "$since_tag" ]]; then
        git log --pretty=format:"- %s ([%h](../../commit/%H))" "$since_tag..HEAD" >> "$temp_changelog"
    else
        git log --pretty=format:"- %s ([%h](../../commit/%H))" >> "$temp_changelog"
    fi
    
    echo "" >> "$temp_changelog"
    echo "" >> "$temp_changelog"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN] Would add the following to changelog:${NC}"
        cat "$temp_changelog"
        rm "$temp_changelog"
        return
    fi
    
    # Insert new changelog entry
    if [[ -f "$CHANGELOG_FILE" ]]; then
        # Find the line after the header and insert
        local header_line=$(grep -n "# Changelog" "$CHANGELOG_FILE" | head -1 | cut -d: -f1)
        if [[ -n "$header_line" ]]; then
            local insert_line=$((header_line + 2))
            # Create temporary file with new content
            head -n "$insert_line" "$CHANGELOG_FILE" > "${CHANGELOG_FILE}.tmp"
            cat "$temp_changelog" >> "${CHANGELOG_FILE}.tmp"
            tail -n +$((insert_line + 1)) "$CHANGELOG_FILE" >> "${CHANGELOG_FILE}.tmp"
            mv "${CHANGELOG_FILE}.tmp" "$CHANGELOG_FILE"
        else
            # No header found, prepend to file
            cat "$temp_changelog" "$CHANGELOG_FILE" > "${CHANGELOG_FILE}.tmp"
            mv "${CHANGELOG_FILE}.tmp" "$CHANGELOG_FILE"
        fi
    else
        # Create new changelog
        cat > "$CHANGELOG_FILE" << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

EOF
        cat "$temp_changelog" >> "$CHANGELOG_FILE"
    fi
    
    rm "$temp_changelog"
    echo -e "${GREEN}✓ Changelog updated${NC}"
}

# Function to run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        echo -e "${YELLOW}Skipping tests${NC}"
        return
    fi
    
    echo -e "${YELLOW}Running tests...${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN] Would run tests${NC}"
        return
    fi
    
    # Run different test commands based on project type
    if [[ -f "pytest.ini" ]] || [[ -f "pyproject.toml" ]]; then
        $PYTHON_CMD -m pytest -v
    elif [[ -f "package.json" ]]; then
        npm test
    elif [[ -f "Makefile" ]]; then
        make test
    else
        echo -e "${YELLOW}No test configuration found, skipping tests${NC}"
        return
    fi
    
    echo -e "${GREEN}✓ All tests passed${NC}"
}

# Function to build artifacts
build_artifacts() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        echo -e "${YELLOW}Skipping build${NC}"
        return
    fi
    
    echo -e "${YELLOW}Building artifacts...${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN] Would build artifacts${NC}"
        return
    fi
    
    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/
    
    # Build based on project type
    if [[ -f "pyproject.toml" ]]; then
        $PYTHON_CMD -m pip install --upgrade build
        $PYTHON_CMD -m build
    elif [[ -f "setup.py" ]]; then
        $PYTHON_CMD setup.py sdist bdist_wheel
    elif [[ -f "package.json" ]]; then
        npm run build
    elif [[ -f "Makefile" ]]; then
        make build
    else
        echo -e "${YELLOW}No build configuration found, skipping build${NC}"
        return
    fi
    
    echo -e "${GREEN}✓ Artifacts built successfully${NC}"
}

# Function to build Docker image
build_docker() {
    if [[ "$SKIP_DOCKER" == "true" ]]; then
        echo -e "${YELLOW}Skipping Docker build${NC}"
        return
    fi
    
    if [[ ! -f "Dockerfile" ]]; then
        echo -e "${YELLOW}No Dockerfile found, skipping Docker build${NC}"
        return
    fi
    
    local version="$1"
    local image_name="${DOCKER_IMAGE_NAME:-$(basename $(pwd))}"
    
    echo -e "${YELLOW}Building Docker image...${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN] Would build Docker image: $image_name:$version${NC}"
        return
    fi
    
    docker build -t "$image_name:$version" -t "$image_name:latest" .
    
    echo -e "${GREEN}✓ Docker image built: $image_name:$version${NC}"
}

# Function to create release commit and tag
create_release_commit() {
    local version="$1"
    
    echo -e "${YELLOW}Creating release commit and tag...${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN] Would create commit and tag v$version${NC}"
        return
    fi
    
    # Add changed files
    git add "$VERSION_FILE" "$CHANGELOG_FILE"
    
    # Create release commit
    git commit -m "chore(release): bump version to $version

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    # Create annotated tag
    git tag -a "v$version" -m "Release version $version

$(git log --pretty=format:"- %s" $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~10)..HEAD | head -10)

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    echo -e "${GREEN}✓ Created release commit and tag v$version${NC}"
}

# Function to push changes
push_changes() {
    local version="$1"
    
    echo -e "${YELLOW}Pushing changes to remote...${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN] Would push changes and tag v$version${NC}"
        return
    fi
    
    # Push commit and tag
    git push origin "$CURRENT_BRANCH"
    git push origin "v$version"
    
    echo -e "${GREEN}✓ Changes pushed to remote${NC}"
}

# Function to create GitHub release
create_github_release() {
    local version="$1"
    
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}GitHub CLI not found, skipping GitHub release${NC}"
        return
    fi
    
    echo -e "${YELLOW}Creating GitHub release...${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN] Would create GitHub release v$version${NC}"
        return
    fi
    
    # Extract changelog for this version
    local release_notes=""
    if [[ -f "$CHANGELOG_FILE" ]]; then
        # Extract the section for this version
        release_notes=$(awk "/## \[$version\]/,/## \[/{if(/## \[/ && !/## \[$version\]/) exit; if(!/## \[$version\]/) print}" "$CHANGELOG_FILE")
    fi
    
    if [[ -z "$release_notes" ]]; then
        release_notes="Release version $version"
    fi
    
    # Create release with artifacts
    local release_args="--title \"Release v$version\" --notes \"$release_notes\""
    
    # Add artifacts if they exist
    if [[ -d "dist" ]]; then
        release_args="$release_args dist/*"
    fi
    
    eval "gh release create \"v$version\" $release_args"
    
    echo -e "${GREEN}✓ GitHub release created${NC}"
}

# Function to merge to main branch
merge_to_main() {
    local version="$1"
    
    if [[ "$AUTO_MERGE" != "true" ]]; then
        echo -e "${YELLOW}Auto-merge disabled, skipping merge to main${NC}"
        return
    fi
    
    if [[ "$CURRENT_BRANCH" == "$DEFAULT_BRANCH" ]]; then
        echo -e "${YELLOW}Already on main branch, skipping merge${NC}"
        return
    fi
    
    echo -e "${YELLOW}Merging to $DEFAULT_BRANCH...${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN] Would merge to $DEFAULT_BRANCH${NC}"
        return
    fi
    
    # Switch to main branch
    git checkout "$DEFAULT_BRANCH"
    git pull origin "$DEFAULT_BRANCH"
    
    # Merge release branch
    git merge --no-ff "$CURRENT_BRANCH" -m "Merge release v$version into $DEFAULT_BRANCH"
    
    # Push main branch
    git push origin "$DEFAULT_BRANCH"
    
    echo -e "${GREEN}✓ Merged to $DEFAULT_BRANCH${NC}"
}

# Function to show release summary
show_release_summary() {
    local old_version="$1"
    local new_version="$2"
    
    echo ""
    echo -e "${BLUE}=== Release Summary ===${NC}"
    echo -e "Previous version: $old_version"
    echo -e "New version: $new_version"
    echo -e "Branch: $CURRENT_BRANCH"
    echo -e "Tag: v$new_version"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}This was a dry run - no changes were made${NC}"
    else
        echo -e "${GREEN}Release completed successfully!${NC}"
    fi
    
    echo ""
    echo -e "Next steps:"
    echo -e "- Review the release at: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases/tag/v$new_version"
    echo -e "- Monitor deployment and system health"
    echo -e "- Update documentation if needed"
}

# Function to rollback release
rollback_release() {
    local version="$1"
    
    echo -e "${YELLOW}Rolling back release v$version...${NC}"
    
    # Remove tag
    if git tag -l "v$version" | grep -q "v$version"; then
        git tag -d "v$version"
        git push origin ":refs/tags/v$version" 2>/dev/null || true
    fi
    
    # Reset to previous commit
    git reset --hard HEAD~1
    
    echo -e "${GREEN}✓ Release v$version rolled back${NC}"
}

# Main release function
main() {
    local increment_type="${1:-}"
    local force_version="${2:-}"
    
    # Validate arguments
    if [[ -z "$increment_type" ]] && [[ -z "$force_version" ]]; then
        echo "Usage: $0 <increment_type|version> [force_version]"
        echo ""
        echo "Increment types:"
        echo "  major    - Increment major version (breaking changes)"
        echo "  minor    - Increment minor version (new features)"
        echo "  patch    - Increment patch version (bug fixes)"
        echo "  auto     - Auto-detect based on commit messages"
        echo ""
        echo "Or specify exact version:"
        echo "  $0 1.2.3"
        echo ""
        echo "Environment variables:"
        echo "  DRY_RUN=true          - Preview changes without executing"
        echo "  SKIP_TESTS=true       - Skip running tests"
        echo "  SKIP_BUILD=true       - Skip building artifacts"
        echo "  SKIP_DOCKER=true      - Skip Docker build"
        echo "  AUTO_MERGE=true       - Automatically merge to main branch"
        exit 1
    fi
    
    # Pre-flight checks
    check_git_repo
    check_clean_working_tree
    check_branch_sync "$CURRENT_BRANCH"
    
    # Get current version
    local current_version
    current_version=$(get_current_version)
    echo -e "Current version: $current_version"
    
    # Determine new version
    local new_version
    if [[ "$increment_type" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        # Exact version specified
        new_version="$increment_type"
    elif [[ "$increment_type" == "auto" ]]; then
        # Auto-detect increment type
        local last_tag
        last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
        local detected_increment
        detected_increment=$(detect_version_increment "$last_tag")
        new_version=$(increment_version "$current_version" "$detected_increment")
        echo -e "Auto-detected increment type: $detected_increment"
    else
        # Manual increment type
        new_version=$(increment_version "$current_version" "$increment_type")
    fi
    
    echo -e "New version: $new_version"
    
    # Confirmation
    if [[ "$DRY_RUN" != "true" ]]; then
        echo ""
        read -p "Proceed with release v$new_version? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Release cancelled${NC}"
            exit 0
        fi
    fi
    
    # Release process
    echo ""
    echo -e "${BLUE}Starting release process...${NC}"
    
    # Trap for cleanup on error
    trap 'echo -e "${RED}Release failed! Rolling back...${NC}"; rollback_release "$new_version" 2>/dev/null || true' ERR
    
    # Execute release steps
    run_tests
    build_artifacts
    build_docker "$new_version"
    update_version_file "$new_version"
    
    # Get last tag for changelog
    local last_tag
    last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    generate_changelog "$new_version" "$last_tag"
    
    create_release_commit "$new_version"
    push_changes "$new_version"
    create_github_release "$new_version"
    merge_to_main "$new_version"
    
    # Clear trap
    trap - ERR
    
    # Show summary
    show_release_summary "$current_version" "$new_version"
}

# Handle special commands
case "${1:-}" in
    "--help"|"-h")
        main
        ;;
    "--rollback")
        if [[ -z "${2:-}" ]]; then
            echo "Usage: $0 --rollback <version>"
            exit 1
        fi
        rollback_release "$2"
        ;;
    *)
        main "$@"
        ;;
esac