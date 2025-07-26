#!/bin/bash
# Repository Hygiene Bot Runner
# 
# Usage:
#   ./run_hygiene.sh                    # Process all repositories
#   ./run_hygiene.sh --repo my-repo     # Process specific repository
#   ./run_hygiene.sh --dry-run          # Show what would be done
#
# Environment variables:
#   GITHUB_TOKEN - GitHub personal access token (required)

set -e

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable is required"
    echo "Generate a token at: https://github.com/settings/tokens"
    echo "Required scopes: repo, user, admin:org"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv-hygiene" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv-hygiene
    source venv-hygiene/bin/activate
    pip install -r requirements-hygiene.txt
else
    source venv-hygiene/bin/activate
fi

# Run the hygiene bot
echo "Running repository hygiene bot..."
python3 repo_hygiene_bot.py "$@"

echo "Repository hygiene check complete!"