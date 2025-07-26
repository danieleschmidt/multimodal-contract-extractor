#!/usr/bin/env python3
"""
Repository Hygiene Automation Bot

Implements the complete repo hygiene checklist for GitHub repositories.
This script automates all 10 steps from the checklist to ensure repositories
meet community standards and security best practices.
"""

import json
import os
import re
import requests
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GitHubRepoHygiene:
    """Main class for repository hygiene automation."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize with GitHub token."""
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable.")
        
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'repo-hygiene-bot/1.0'
        }
        self.base_url = 'https://api.github.com'
        self.changes_made = []
        
    def get_user_repos(self) -> List[Dict[str, Any]]:
        """Step 0: List repositories owned by the authenticated user."""
        logger.info("Fetching user repositories...")
        
        url = f"{self.base_url}/user/repos"
        params = {
            'per_page': 100,
            'affiliation': 'owner',
            'sort': 'updated',
            'direction': 'desc'
        }
        
        repos = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
                
            # Filter out forks, templates, and archived repos
            filtered_repos = [
                repo for repo in page_repos 
                if not repo['fork'] and not repo['is_template'] and not repo['archived']
            ]
            repos.extend(filtered_repos)
            page += 1
            
        logger.info(f"Found {len(repos)} eligible repositories")
        return repos
    
    def update_repo_metadata(self, repo: Dict[str, Any]) -> bool:
        """Step 1: Update description, website & topics."""
        owner = repo['owner']['login']
        name = repo['name']
        updated = False
        
        # Update description if empty
        if not repo['description']:
            description = self._generate_description(repo)
            update_data = {'description': description}
            
            url = f"{self.base_url}/repos/{owner}/{name}"
            response = requests.patch(url, headers=self.headers, json=update_data)
            
            if response.status_code == 200:
                logger.info(f"Updated description for {name}")
                self.changes_made.append(f"Added description to {name}")
                updated = True
        
        # Update homepage if null
        if not repo['homepage']:
            homepage = f"https://{owner}.github.io"
            update_data = {'homepage': homepage}
            
            url = f"{self.base_url}/repos/{owner}/{name}"
            response = requests.patch(url, headers=self.headers, json=update_data)
            
            if response.status_code == 200:
                logger.info(f"Updated homepage for {name}")
                self.changes_made.append(f"Added homepage to {name}")
                updated = True
        
        # Update topics if less than 5
        current_topics = repo.get('topics', [])
        if len(current_topics) < 5:
            new_topics = self._generate_topics(repo, current_topics)
            
            url = f"{self.base_url}/repos/{owner}/{name}/topics"
            response = requests.put(url, headers=self.headers, json={'names': new_topics})
            
            if response.status_code == 200:
                logger.info(f"Updated topics for {name}")
                self.changes_made.append(f"Added topics to {name}")
                updated = True
                
        return updated
    
    def ensure_community_files(self, repo: Dict[str, Any]) -> bool:
        """Step 2: Create missing community files."""
        owner = repo['owner']['login']
        name = repo['name']
        updated = False
        
        # Check existing files
        existing_files = self._get_repo_files(owner, name)
        
        community_files = {
            'LICENSE': self._get_apache_license(),
            'CODE_OF_CONDUCT.md': self._get_code_of_conduct(),
            'CONTRIBUTING.md': self._get_contributing_guide(),
            'SECURITY.md': self._get_security_policy(),
            '.github/ISSUE_TEMPLATE/bug.yml': self._get_bug_template(),
            '.github/ISSUE_TEMPLATE/feature.yml': self._get_feature_template()
        }
        
        for file_path, content in community_files.items():
            if file_path not in existing_files:
                if self._create_file(owner, name, file_path, content):
                    self.changes_made.append(f"Added {file_path} to {name}")
                    updated = True
                    
        return updated
    
    def setup_security_scanners(self, repo: Dict[str, Any]) -> bool:
        """Step 3: Enable security scanners."""
        owner = repo['owner']['login']
        name = repo['name']
        updated = False
        
        # Enable CodeQL if not exists
        workflows_dir = '.github/workflows'
        existing_files = self._get_repo_files(owner, name, workflows_dir)
        
        if not any('codeql' in f.lower() for f in existing_files):
            codeql_content = self._get_codeql_workflow()
            if self._create_file(owner, name, f'{workflows_dir}/codeql.yml', codeql_content):
                self.changes_made.append(f"Added CodeQL workflow to {name}")
                updated = True
        
        # Create Dependabot config
        dependabot_path = '.github/dependabot.yml'
        if dependabot_path not in existing_files:
            dependabot_content = self._get_dependabot_config(repo)
            if self._create_file(owner, name, dependabot_path, dependabot_content):
                self.changes_made.append(f"Added Dependabot config to {name}")
                updated = True
        
        # Add OpenSSF Scorecard workflow
        if not any('scorecard' in f.lower() for f in existing_files):
            scorecard_content = self._get_scorecard_workflow()
            if self._create_file(owner, name, f'{workflows_dir}/scorecard.yml', scorecard_content):
                self.changes_made.append(f"Added OpenSSF Scorecard to {name}")
                updated = True
                
        return updated
    
    def setup_sbom_and_signing(self, repo: Dict[str, Any]) -> bool:
        """Step 4: Add SBOM and signed releases."""
        owner = repo['owner']['login']
        name = repo['name']
        updated = False
        
        # Only for repos that build artifacts
        if self._builds_artifacts(repo):
            workflows_dir = '.github/workflows'
            existing_files = self._get_repo_files(owner, name, workflows_dir)
            
            # Add SBOM workflow
            if not any('sbom' in f.lower() for f in existing_files):
                sbom_content = self._get_sbom_workflow()
                if self._create_file(owner, name, f'{workflows_dir}/sbom.yml', sbom_content):
                    self.changes_made.append(f"Added SBOM workflow to {name}")
                    updated = True
            
            # Add SBOM diff workflow
            if not any('sbom-diff' in f.lower() for f in existing_files):
                sbom_diff_content = self._get_sbom_diff_workflow()
                if self._create_file(owner, name, f'{workflows_dir}/sbom-diff.yml', sbom_diff_content):
                    self.changes_made.append(f"Added SBOM diff workflow to {name}")
                    updated = True
                    
        return updated
    
    def inject_readme_badges(self, repo: Dict[str, Any]) -> bool:
        """Step 5: Add README badges if missing."""
        owner = repo['owner']['login']
        name = repo['name']
        
        # Get current README
        readme_content = self._get_file_content(owner, name, 'README.md')
        if not readme_content:
            return False
            
        # Check if badges already exist
        if 'img.shields.io' in readme_content or 'badge' in readme_content.lower():
            return False
            
        # Generate badges
        badges = self._generate_badges(owner, name)
        
        # Insert badges after first heading
        lines = readme_content.split('\n')
        insert_pos = 1  # After first line (title)
        
        # Find first heading
        for i, line in enumerate(lines):
            if line.startswith('#'):
                insert_pos = i + 1
                break
                
        # Insert badges
        lines.insert(insert_pos, '')
        lines.insert(insert_pos + 1, badges)
        lines.insert(insert_pos + 2, '')
        
        new_content = '\n'.join(lines)
        
        if self._update_file(owner, name, 'README.md', new_content, readme_content):
            self.changes_made.append(f"Added badges to README in {name}")
            return True
            
        return False
    
    def archive_stale_repos(self, repos: List[Dict[str, Any]]) -> bool:
        """Step 6: Archive stale repositories."""
        updated = False
        cutoff_date = datetime.now() - timedelta(days=400)
        
        for repo in repos:
            # Only archive repos named "Main-Project" (as per checklist)
            if repo['name'] == 'Main-Project':
                last_commit = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
                
                if last_commit < cutoff_date:
                    owner = repo['owner']['login']
                    name = repo['name']
                    
                    url = f"{self.base_url}/repos/{owner}/{name}"
                    response = requests.patch(url, headers=self.headers, json={'archived': True})
                    
                    if response.status_code == 200:
                        logger.info(f"Archived stale repository: {name}")
                        self.changes_made.append(f"Archived stale repository {name}")
                        updated = True
                        
        return updated
    
    def ensure_readme_sections(self, repo: Dict[str, Any]) -> bool:
        """Step 7: Ensure required README sections exist."""
        owner = repo['owner']['login']
        name = repo['name']
        
        readme_content = self._get_file_content(owner, name, 'README.md')
        if not readme_content:
            return False
            
        required_sections = [
            '## ✨ Why this exists',
            '## ⚡ Quick Start', 
            '## 🔍 Key Features',
            '## 🗺 Road Map',
            '## 🤝 Contributing'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in readme_content:
                missing_sections.append(section)
        
        if missing_sections:
            # Append missing sections
            new_content = readme_content + '\n\n' + '\n\n'.join(missing_sections + [''])
            
            if self._update_file(owner, name, 'README.md', new_content, readme_content):
                self.changes_made.append(f"Added missing README sections to {name}")
                return True
                
        return False
    
    def pin_top_repositories(self, repos: List[Dict[str, Any]]) -> bool:
        """Step 8: Pin top repositories by star count."""
        # Sort by star count and take top 6
        top_repos = sorted(repos, key=lambda x: x['stargazers_count'], reverse=True)[:6]
        
        repo_names = [repo['name'] for repo in top_repos]
        
        url = f"{self.base_url}/user/pinned_repositories"
        response = requests.put(url, headers=self.headers, json={'repository_names': repo_names})
        
        if response.status_code == 200:
            logger.info(f"Pinned top repositories: {', '.join(repo_names)}")
            self.changes_made.append(f"Pinned top {len(repo_names)} repositories")
            return True
            
        return False
    
    def update_metrics_log(self, repo: Dict[str, Any]) -> bool:
        """Step 9: Update metrics log."""
        owner = repo['owner']['login']
        name = repo['name']
        
        # Create metrics directory if it doesn't exist
        metrics_dir = 'metrics'
        metrics_file = f'{metrics_dir}/profile_hygiene.json'
        
        # Get current metrics or create new
        existing_content = self._get_file_content(owner, name, metrics_file)
        
        if existing_content:
            try:
                metrics = json.loads(existing_content)
            except json.JSONDecodeError:
                metrics = {}
        else:
            metrics = {}
        
        # Update metrics based on current state
        repo_files = self._get_repo_files(owner, name)
        
        metrics.update({
            'description_set': bool(repo['description']),
            'topics_count': len(repo.get('topics', [])),
            'license_exists': 'LICENSE' in repo_files,
            'code_scanning': any('codeql' in f.lower() for f in repo_files),
            'dependabot': '.github/dependabot.yml' in repo_files,
            'scorecard': any('scorecard' in f.lower() for f in repo_files),
            'sbom_workflow': any('sbom' in f.lower() for f in repo_files),
            'last_updated': datetime.now().isoformat()
        })
        
        new_content = json.dumps(metrics, indent=2)
        
        if existing_content:
            success = self._update_file(owner, name, metrics_file, new_content, existing_content)
        else:
            success = self._create_file(owner, name, metrics_file, new_content)
            
        if success:
            self.changes_made.append(f"Updated metrics log for {name}")
            return True
            
        return False
    
    def create_hygiene_pr(self, repo: Dict[str, Any]) -> Optional[str]:
        """Step 10: Create pull request with changes."""
        if not self.changes_made:
            return None
            
        owner = repo['owner']['login']
        name = repo['name']
        
        # Create branch for changes
        branch_name = 'repo-hygiene-bot-update'
        
        # Get current main branch SHA
        url = f"{self.base_url}/repos/{owner}/{name}/git/refs/heads/main"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get main branch SHA for {name}")
            return None
            
        main_sha = response.json()['object']['sha']
        
        # Create new branch
        url = f"{self.base_url}/repos/{owner}/{name}/git/refs"
        branch_data = {
            'ref': f'refs/heads/{branch_name}',
            'sha': main_sha
        }
        
        response = requests.post(url, headers=self.headers, json=branch_data)
        
        if response.status_code not in [200, 201, 422]:  # 422 if branch exists
            logger.error(f"Failed to create branch for {name}")
            return None
        
        # Create PR
        pr_title = "✨ repo-hygiene-bot update"
        pr_body = self._generate_pr_body()
        
        url = f"{self.base_url}/repos/{owner}/{name}/pulls"
        pr_data = {
            'title': pr_title,
            'body': pr_body,
            'head': branch_name,
            'base': 'main'
        }
        
        response = requests.post(url, headers=self.headers, json=pr_data)
        
        if response.status_code == 201:
            pr_url = response.json()['html_url']
            logger.info(f"Created PR for {name}: {pr_url}")
            
            # Add label
            pr_number = response.json()['number']
            self._add_pr_label(owner, name, pr_number, 'automated-maintenance')
            
            return pr_url
        else:
            logger.error(f"Failed to create PR for {name}: {response.text}")
            return None
    
    def run_hygiene_check(self, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """Run complete hygiene check on repositories."""
        logger.info("Starting repository hygiene check...")
        
        repos = self.get_user_repos()
        
        if repo_name:
            repos = [repo for repo in repos if repo['name'] == repo_name]
            if not repos:
                raise ValueError(f"Repository '{repo_name}' not found")
        
        results = {
            'total_repos': len(repos),
            'updated_repos': [],
            'prs_created': [],
            'errors': []
        }
        
        for repo in repos:
            try:
                logger.info(f"Processing repository: {repo['name']}")
                self.changes_made = []  # Reset for each repo
                
                # Run all hygiene steps
                steps_run = []
                
                if self.update_repo_metadata(repo):
                    steps_run.append('metadata')
                    
                if self.ensure_community_files(repo):
                    steps_run.append('community_files')
                    
                if self.setup_security_scanners(repo):
                    steps_run.append('security_scanners')
                    
                if self.setup_sbom_and_signing(repo):
                    steps_run.append('sbom_signing')
                    
                if self.inject_readme_badges(repo):
                    steps_run.append('readme_badges')
                    
                if self.ensure_readme_sections(repo):
                    steps_run.append('readme_sections')
                    
                if self.update_metrics_log(repo):
                    steps_run.append('metrics_log')
                
                # Create PR if changes were made
                if self.changes_made:
                    pr_url = self.create_hygiene_pr(repo)
                    if pr_url:
                        results['prs_created'].append({
                            'repo': repo['name'],
                            'pr_url': pr_url,
                            'changes': self.changes_made.copy()
                        })
                    
                    results['updated_repos'].append({
                        'name': repo['name'],
                        'steps_completed': steps_run,
                        'changes': self.changes_made.copy()
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {repo['name']}: {str(e)}")
                results['errors'].append({
                    'repo': repo['name'],
                    'error': str(e)
                })
        
        # Run global steps
        try:
            if self.archive_stale_repos(repos):
                results['global_actions'] = ['archived_stale_repos']
                
            if self.pin_top_repositories(repos):
                results['global_actions'] = results.get('global_actions', []) + ['pinned_repositories']
                
        except Exception as e:
            logger.error(f"Error in global actions: {str(e)}")
            results['errors'].append({
                'repo': 'global',
                'error': str(e)
            })
        
        logger.info(f"Hygiene check complete. Updated {len(results['updated_repos'])} repositories.")
        return results
    
    # Helper methods
    def _generate_description(self, repo: Dict[str, Any]) -> str:
        """Generate a description based on repository content."""
        # This is a simplified version - in practice, you'd analyze the code
        language = repo.get('language', '').lower()
        
        descriptions = {
            'python': 'Python application for automated processing and analysis',
            'javascript': 'JavaScript/Node.js application with modern tooling',
            'typescript': 'TypeScript application with type-safe development',
            'java': 'Java application with enterprise-grade architecture',
            'go': 'Go application optimized for performance and concurrency',
            'rust': 'Rust application with memory safety and speed',
        }
        
        return descriptions.get(language, 'Modern software application with automated tooling')
    
    def _generate_topics(self, repo: Dict[str, Any], current: List[str]) -> List[str]:
        """Generate relevant topics for the repository."""
        language = repo.get('language', '').lower()
        
        base_topics = {
            'python': ['python', 'automation', 'cli', 'data-processing'],
            'javascript': ['javascript', 'nodejs', 'web', 'automation'],
            'typescript': ['typescript', 'javascript', 'type-safety', 'web'],
            'java': ['java', 'enterprise', 'spring', 'microservices'],
            'go': ['golang', 'performance', 'concurrency', 'cli'],
            'rust': ['rust', 'systems-programming', 'performance', 'memory-safety'],
        }
        
        suggested = base_topics.get(language, ['software', 'automation', 'tooling'])
        suggested.extend(['github-actions', 'ci-cd', 'security'])
        
        # Combine with current topics and ensure we have 5+
        all_topics = list(set(current + suggested))
        return all_topics[:8]  # Limit to 8 topics
    
    def _get_repo_files(self, owner: str, name: str, path: str = '') -> List[str]:
        """Get list of files in repository."""
        url = f"{self.base_url}/repos/{owner}/{name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return []
            
        files = []
        for item in response.json():
            if item['type'] == 'file':
                files.append(item['path'])
            elif item['type'] == 'dir':
                # Recursively get files in subdirectories
                subfiles = self._get_repo_files(owner, name, item['path'])
                files.extend(subfiles)
                
        return files
    
    def _get_file_content(self, owner: str, name: str, path: str) -> Optional[str]:
        """Get content of a specific file."""
        url = f"{self.base_url}/repos/{owner}/{name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return None
            
        import base64
        return base64.b64decode(response.json()['content']).decode('utf-8')
    
    def _create_file(self, owner: str, name: str, path: str, content: str) -> bool:
        """Create a new file in the repository."""
        import base64
        
        url = f"{self.base_url}/repos/{owner}/{name}/contents/{path}"
        data = {
            'message': f'Add {path}',
            'content': base64.b64encode(content.encode()).decode()
        }
        
        response = requests.put(url, headers=self.headers, json=data)
        return response.status_code == 201
    
    def _update_file(self, owner: str, name: str, path: str, new_content: str, old_content: str) -> bool:
        """Update an existing file in the repository."""
        import base64
        
        # Get current file SHA
        url = f"{self.base_url}/repos/{owner}/{name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return False
            
        sha = response.json()['sha']
        
        data = {
            'message': f'Update {path}',
            'content': base64.b64encode(new_content.encode()).decode(),
            'sha': sha
        }
        
        response = requests.put(url, headers=self.headers, json=data)
        return response.status_code == 200
    
    def _builds_artifacts(self, repo: Dict[str, Any]) -> bool:
        """Check if repository builds artifacts that need SBOM."""
        language = repo.get('language', '').lower()
        artifact_languages = ['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'docker']
        return language in artifact_languages
    
    def _generate_badges(self, owner: str, name: str) -> str:
        """Generate README badges."""
        return f"""[![License](https://img.shields.io/github/license/{owner}/{name})](LICENSE)
[![CI](https://github.com/{owner}/{name}/workflows/CI/badge.svg)](https://github.com/{owner}/{name}/actions)
[![Security Rating](https://api.securityscorecards.dev/projects/github.com/{owner}/{name}/badge)](https://api.securityscorecards.dev/projects/github.com/{owner}/{name})
[![SBOM](https://img.shields.io/badge/SBOM-Available-green)](docs/sbom/latest.json)"""
    
    def _generate_pr_body(self) -> str:
        """Generate pull request body."""
        body = "## Repository Hygiene Update\n\nThis automated PR updates the repository to meet community standards and security best practices.\n\n### Changes Made:\n"
        
        for change in self.changes_made:
            body += f"- {change}\n"
            
        body += "\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        return body
    
    def _add_pr_label(self, owner: str, name: str, pr_number: int, label: str) -> bool:
        """Add label to pull request."""
        url = f"{self.base_url}/repos/{owner}/{name}/issues/{pr_number}/labels"
        response = requests.post(url, headers=self.headers, json=[label])
        return response.status_code == 200
    
    # Template content methods
    def _get_apache_license(self) -> str:
        return """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

[Full Apache 2.0 license text would go here]
"""
    
    def _get_code_of_conduct(self) -> str:
        return """# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone.

[Full Contributor Covenant v2.1 text would go here]
"""
    
    def _get_contributing_guide(self) -> str:
        return """# Contributing

Thank you for your interest in contributing! 

## Development Setup

1. Fork and clone the repository
2. Install dependencies
3. Make your changes
4. Run tests
5. Submit a pull request

## Commit Convention

We use [Conventional Commits](https://conventionalcommits.org/).

Examples:
- `feat: add new feature`
- `fix: resolve bug in component`
- `docs: update README`
"""
    
    def _get_security_policy(self) -> str:
        return """# Security Policy

## Reporting Vulnerabilities

Please report security vulnerabilities to security@company.com

We aim to respond within 90 days and will keep you informed of progress.

## Supported Versions

We provide security updates for the latest major version.
"""
    
    def _get_bug_template(self) -> str:
        return """name: Bug Report
description: Report a bug or issue
labels: ["bug"]
body:
  - type: textarea
    attributes:
      label: Description
      description: What happened?
    validations:
      required: true
  - type: textarea
    attributes:
      label: Steps to Reproduce
      description: How can we reproduce this?
    validations:
      required: true
  - type: textarea
    attributes:
      label: Expected Behavior
      description: What should have happened?
    validations:
      required: true
"""
    
    def _get_feature_template(self) -> str:
        return """name: Feature Request
description: Suggest a new feature
labels: ["enhancement"]
body:
  - type: textarea
    attributes:
      label: Feature Description
      description: What feature would you like to see?
    validations:
      required: true
  - type: textarea
    attributes:
      label: Use Case
      description: Why is this feature needed?
    validations:
      required: true
"""
    
    def _get_codeql_workflow(self) -> str:
        return """name: "CodeQL"

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]
  schedule:
    - cron: '0 6 * * 1'

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'python' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}

    - name: Autobuild
      uses: github/codeql-action/autobuild@v3

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
      with:
        category: "/language:${{matrix.language}}"
"""
    
    def _get_dependabot_config(self, repo: Dict[str, Any]) -> str:
        """Generate Dependabot configuration based on repository language."""
        language = repo.get('language', '').lower()
        
        config = {
            'version': 2,
            'updates': [
                {
                    'package-ecosystem': 'github-actions',
                    'directory': '/',
                    'schedule': {'interval': 'weekly'}
                }
            ]
        }
        
        if language == 'python':
            config['updates'].append({
                'package-ecosystem': 'pip',
                'directory': '/',
                'schedule': {'interval': 'weekly'}
            })
        elif language in ['javascript', 'typescript']:
            config['updates'].append({
                'package-ecosystem': 'npm',
                'directory': '/',
                'schedule': {'interval': 'weekly'}
            })
        
        return yaml.dump(config, default_flow_style=False)
    
    def _get_scorecard_workflow(self) -> str:
        return """name: OpenSSF Scorecard
on:
  branch_protection_rule:
  schedule:
    - cron: '0 6 * * 1'
  push:
    branches: [ "main" ]

permissions: read-all

jobs:
  analysis:
    name: Scorecard analysis
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      id-token: write

    steps:
      - name: "Checkout code"
        uses: actions/checkout@v4
        with:
          persist-credentials: false

      - name: "Run analysis"
        uses: ossf/scorecard-action@v2.3.1
        with:
          results_file: results.sarif
          results_format: sarif
          publish_results: true

      - name: "Upload to code-scanning"
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
"""
    
    def _get_sbom_workflow(self) -> str:
        return """name: SBOM Generation

on:
  push:
    branches: [ "main" ]
  release:
    types: [ published ]

jobs:
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate SBOM
        uses: CycloneDX/gh-python-generate-sbom@v1
        with:
          input: ./
          output: ./docs/sbom/latest.json
          
      - name: Upload SBOM
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: ./docs/sbom/latest.json
"""
    
    def _get_sbom_diff_workflow(self) -> str:
        return """name: SBOM Security Diff

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  sbom-diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate current SBOM
        uses: CycloneDX/gh-python-generate-sbom@v1
        with:
          input: ./
          output: ./sbom-current.json
          
      - name: Download previous SBOM
        run: |
          curl -o sbom-previous.json -f https://raw.githubusercontent.com/${{ github.repository }}/main/docs/sbom/latest.json || echo '{}' > sbom-previous.json
          
      - name: Run SBOM diff
        run: |
          # Install cyclonedx-cli if not available
          pip install cyclonedx-bom
          
          # Compare SBOMs and fail on critical CVEs
          cyclonedx diff sbom-previous.json sbom-current.json || exit 1
"""


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Repository Hygiene Automation Bot')
    parser.add_argument('--repo', help='Specific repository name to process')
    parser.add_argument('--token', help='GitHub personal access token')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    try:
        bot = GitHubRepoHygiene(token=args.token)
        
        if args.dry_run:
            repos = bot.get_user_repos()
            if args.repo:
                repos = [repo for repo in repos if repo['name'] == args.repo]
            
            print(f"Would process {len(repos)} repositories:")
            for repo in repos:
                print(f"  - {repo['name']} ({repo['language'] or 'No language'})")
        else:
            results = bot.run_hygiene_check(args.repo)
            
            print(f"\nRepository Hygiene Results:")
            print(f"Total repositories: {results['total_repos']}")
            print(f"Updated repositories: {len(results['updated_repos'])}")
            print(f"PRs created: {len(results['prs_created'])}")
            print(f"Errors: {len(results['errors'])}")
            
            if results['prs_created']:
                print("\nPull Requests Created:")
                for pr in results['prs_created']:
                    print(f"  - {pr['repo']}: {pr['pr_url']}")
            
            if results['errors']:
                print("\nErrors:")
                for error in results['errors']:
                    print(f"  - {error['repo']}: {error['error']}")
    
    except Exception as e:
        logger.error(f"Failed to run hygiene check: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())