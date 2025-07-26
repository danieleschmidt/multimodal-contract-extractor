# Repository Hygiene Bot

Automated tool that implements the complete 10-step repository hygiene checklist for GitHub repositories, ensuring they meet community standards and security best practices.

## Features

- **Automated Repository Management**: Updates descriptions, websites, and topics
- **Community Standards**: Creates missing LICENSE, CODE_OF_CONDUCT.md, CONTRIBUTING.md, SECURITY.md
- **Security Scanning**: Sets up CodeQL, Dependabot, and OpenSSF Scorecard
- **SBOM Generation**: Adds Software Bill of Materials workflows for artifact tracking
- **README Enhancement**: Injects badges and ensures required sections exist
- **Metrics Tracking**: Logs hygiene status in JSON format
- **Automated PRs**: Creates pull requests with all changes for review

## Quick Start

1. **Generate GitHub Token**
   - Go to [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens)
   - Create token with scopes: `repo`, `user`, `admin:org`
   - Export as environment variable: `export GITHUB_TOKEN=your_token_here`

2. **Run Hygiene Check**
   ```bash
   # Process all your repositories
   ./run_hygiene.sh
   
   # Process specific repository
   ./run_hygiene.sh --repo multimodal-contract-extractor
   
   # Dry run (see what would be done)
   ./run_hygiene.sh --dry-run
   ```

3. **Review and Merge PRs**
   - Bot creates PR titled "✨ repo-hygiene-bot update"
   - Review changes and merge when satisfied
   - PRs are labeled `automated-maintenance` and assigned to `@danieleschmidt`

## Checklist Implementation

### ✅ Step 0: List Repositories
- Fetches all owned, non-fork, non-archived repositories
- Filters by ownership and activity status

### ✅ Step 1: Description, Website & Topics  
- Adds descriptive text for empty descriptions (<120 chars)
- Sets homepage to `https://{owner}.github.io`
- Ensures 5+ relevant topics based on repository language

### ✅ Step 2: Community Files
- Creates missing community standards files:
  - `LICENSE` (Apache-2.0)
  - `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1)
  - `CONTRIBUTING.md` (Conventional Commits guide)
  - `SECURITY.md` (Vulnerability disclosure policy)
  - `.github/ISSUE_TEMPLATE/bug.yml`
  - `.github/ISSUE_TEMPLATE/feature.yml`

### ✅ Step 3: Security Scanners
- **CodeQL**: Adds workflow for code analysis
- **Dependabot**: Creates `.github/dependabot.yml` with weekly updates
- **OpenSSF Scorecard**: Adds security posture monitoring

### ✅ Step 4: SBOM + Signed Releases
- **SBOM Workflow**: Generates Software Bill of Materials using CycloneDX
- **SBOM Diff**: Nightly workflow to detect new vulnerabilities
- **Cosign Support**: Ready for keyless artifact signing

### ✅ Step 5: README Badges
- Injects standard badges after first heading:
  - License badge
  - CI workflow status
  - Security scorecard rating
  - SBOM availability

### ✅ Step 6: Stale Repository Archive
- Archives repositories named "Main-Project" with no commits >400 days
- Helps maintain clean repository listings

### ✅ Step 7: README Sections
- Ensures these sections exist in README:
  - `## ✨ Why this exists`
  - `## ⚡ Quick Start`
  - `## 🔍 Key Features`
  - `## 🗺 Road Map`
  - `## 🤝 Contributing`

### ✅ Step 8: Pin Top Repositories
- Automatically pins 6 repositories with highest star counts
- Orders by relevance and community engagement

### ✅ Step 9: Metrics Log
- Creates/updates `metrics/profile_hygiene.json` with status flags:
  ```json
  {
    "description_set": true,
    "topics_count": 8,
    "license_exists": true,
    "code_scanning": true,
    "dependabot": true,
    "scorecard": true,
    "sbom_workflow": true,
    "last_updated": "2025-01-24T10:30:00Z"
  }
  ```

### ✅ Step 10: Open Pull Request
- Creates PR with title: `✨ repo-hygiene-bot update`
- Lists all changes made in bullet format
- Adds label `automated-maintenance`
- Assigns to `@danieleschmidt`

## Configuration

### Environment Variables
- `GITHUB_TOKEN` - Required GitHub personal access token
- `HYGIENE_DRY_RUN` - Set to `true` for dry run mode

### Token Permissions Required
- `repo` - Repository access for reading/writing files
- `user` - User profile access for pinning repositories  
- `admin:org` - Organization access (if processing org repos)

## Output Example

```bash
$ ./run_hygiene.sh --repo multimodal-contract-extractor

Repository Hygiene Results:
Total repositories: 1
Updated repositories: 1
PRs created: 1
Errors: 0

Pull Requests Created:
  - multimodal-contract-extractor: https://github.com/danieleschmidt/multimodal-contract-extractor/pull/42
```

## Advanced Usage

### Python API
```python
from repo_hygiene_bot import GitHubRepoHygiene

bot = GitHubRepoHygiene(token='your_token')
results = bot.run_hygiene_check('specific-repo')

print(f"Updated {len(results['updated_repos'])} repositories")
```

### Custom Templates
The bot includes templates for all community files that can be customized by modifying the `_get_*` methods in the `GitHubRepoHygiene` class.

### Language-Specific Features
- **Python**: Adds pip Dependabot updates, Python-specific SBOM generation
- **JavaScript/TypeScript**: Adds npm Dependabot updates, Node.js workflows
- **Docker**: Adds Docker image security scanning
- **Go/Rust/Java**: Language-specific dependency management

## Security Considerations

- **Token Security**: Bot requires minimal necessary permissions
- **Read-Only Operations**: Most operations are read-only with explicit write confirmation
- **Branch Protection**: Creates feature branches instead of direct commits to main
- **Audit Trail**: All changes tracked in PR descriptions and metrics logs

## Troubleshooting

### Common Issues

1. **Token Permissions**
   ```
   Error: 403 Forbidden
   Solution: Ensure token has required scopes (repo, user, admin:org)
   ```

2. **Rate Limiting**
   ```
   Error: 429 Too Many Requests  
   Solution: Bot includes automatic retry with exponential backoff
   ```

3. **Repository Access**
   ```
   Error: Repository not found
   Solution: Ensure token has access to the repository and it's not archived
   ```

### Debug Mode
Add `--debug` flag for verbose logging:
```bash
./run_hygiene.sh --debug --repo my-repo
```

## Contributing

This bot follows its own hygiene standards! Contributions welcome:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-check`
3. Make changes following existing patterns
4. Add tests for new functionality
5. Submit pull request

## License

Apache-2.0 License - see [LICENSE](LICENSE) file for details.

---

🤖 This tool helps maintain the Terragon Labs ecosystem by ensuring all repositories meet modern community and security standards.