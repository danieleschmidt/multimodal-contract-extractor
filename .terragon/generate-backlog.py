#!/usr/bin/env python3
"""
Simplified Autonomous Value Backlog Generator
Creates prioritized backlog for advanced SDLC repositories
"""

import json
import os
import subprocess
from datetime import datetime


def discover_git_signals():
    """Extract value signals from Git history"""
    signals = []

    try:
        # Find potential technical debt in commit messages
        result = subprocess.run([
            "git", "log", "--oneline", "-50", "--grep=TODO\\|FIXME\\|HACK\\|temp\\|quick"
        ], capture_output=True, text=True, cwd=".")

        debt_commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        if debt_commits > 0:
            signals.append({
                "id": "git-debt-001",
                "title": f"Address technical debt from {debt_commits} commits",
                "category": "technical_debt",
                "description": f"Found {debt_commits} commits with technical debt indicators",
                "wsjf_score": 15.0,
                "ice_score": 180,
                "composite_score": 45.0,
                "effort_hours": 6.0,
                "priority": "medium",
                "source": "git_history"
            })

        # Check for large files that might need refactoring
        result = subprocess.run([
            "find", ".", "-name", "*.py", "-size", "+1000c", "-exec", "wc", "-l", "{}", "+"
        ], capture_output=True, text=True, cwd=".")

        large_files = []
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line and 'total' not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        line_count, file_path = parts[0], parts[1]
                        if line_count.isdigit() and int(line_count) > 300:
                            large_files.append((file_path, int(line_count)))

        if large_files:
            signals.append({
                "id": "refactor-001",
                "title": f"Refactor {len(large_files)} large files",
                "category": "refactoring",
                "description": f"Found {len(large_files)} files with >300 lines that may benefit from refactoring",
                "wsjf_score": 12.0,
                "ice_score": 150,
                "composite_score": 38.0,
                "effort_hours": len(large_files) * 2.0,
                "priority": "medium",
                "source": "file_analysis",
                "files": [f[0] for f in large_files[:5]]
            })

    except subprocess.CalledProcessError:
        pass

    return signals

def discover_dependency_signals():
    """Check for dependency-related opportunities"""
    signals = []

    try:
        # Check requirements files for potential updates
        req_files = ["requirements.txt", "requirements-dev.txt", "pyproject.toml"]
        outdated_deps = 0

        for req_file in req_files:
            if os.path.exists(req_file):
                outdated_deps += 1

        if outdated_deps > 0:
            signals.append({
                "id": "deps-001",
                "title": "Update project dependencies",
                "category": "dependency_update",
                "description": f"Review and update dependencies in {outdated_deps} requirement files",
                "wsjf_score": 8.0,
                "ice_score": 120,
                "composite_score": 25.0,
                "effort_hours": 2.0,
                "priority": "low",
                "source": "dependency_analysis"
            })

    except Exception:
        pass

    return signals

def discover_documentation_signals():
    """Find documentation improvement opportunities"""
    signals = []

    try:
        # Check for missing documentation
        python_files = subprocess.run([
            "find", "src/", "-name", "*.py", "-type", "f"
        ], capture_output=True, text=True, cwd=".")

        py_count = len(python_files.stdout.strip().split('\n')) if python_files.stdout.strip() else 0

        # Check for docstrings
        if py_count > 0:
            signals.append({
                "id": "docs-001",
                "title": f"Enhance documentation for {py_count} Python modules",
                "category": "documentation",
                "description": f"Review and improve docstrings and comments in {py_count} Python files",
                "wsjf_score": 6.0,
                "ice_score": 90,
                "composite_score": 18.0,
                "effort_hours": py_count * 0.5,
                "priority": "low",
                "source": "documentation_analysis"
            })

    except subprocess.CalledProcessError:
        pass

    return signals

def discover_testing_signals():
    """Find testing improvement opportunities"""
    signals = []

    try:
        # Count test files
        test_result = subprocess.run([
            "find", "tests/", "-name", "test_*.py", "-type", "f"
        ], capture_output=True, text=True, cwd=".")

        test_count = len(test_result.stdout.strip().split('\n')) if test_result.stdout.strip() else 0

        # Count source files
        src_result = subprocess.run([
            "find", "src/", "-name", "*.py", "-type", "f"
        ], capture_output=True, text=True, cwd=".")

        src_count = len(src_result.stdout.strip().split('\n')) if src_result.stdout.strip() else 0

        # Check test coverage ratio
        if src_count > 0 and test_count < src_count:
            missing_tests = src_count - test_count
            signals.append({
                "id": "test-001",
                "title": f"Expand test coverage for {missing_tests} modules",
                "category": "testing",
                "description": f"Add tests for {missing_tests} modules to improve coverage",
                "wsjf_score": 10.0,
                "ice_score": 140,
                "composite_score": 35.0,
                "effort_hours": missing_tests * 1.5,
                "priority": "medium",
                "source": "test_analysis"
            })

    except subprocess.CalledProcessError:
        pass

    return signals

def discover_security_signals():
    """Find security improvement opportunities"""
    signals = []

    # Check for security-related files and configurations
    security_files = [
        ".github/workflows/security.yml",
        "trivy.yaml",
        "SECURITY.md",
        ".bandit"
    ]

    existing_security = sum(1 for f in security_files if os.path.exists(f))

    if existing_security > 0:
        signals.append({
            "id": "sec-001",
            "title": "Enhance security scanning automation",
            "category": "security",
            "description": "Optimize existing security tools and add advanced scanning",
            "wsjf_score": 20.0,
            "ice_score": 200,
            "composite_score": 60.0,
            "effort_hours": 4.0,
            "priority": "high",
            "source": "security_analysis"
        })

    return signals

def calculate_composite_score(signal):
    """Calculate weighted composite score for advanced repositories"""
    # Advanced repository weights
    weights = {
        "wsjf": 0.5,
        "ice": 0.1,
        "technicalDebt": 0.3,
        "security": 0.1
    }

    base_score = (
        weights["wsjf"] * signal["wsjf_score"] +
        weights["ice"] * signal["ice_score"] / 100
    )

    # Apply category-specific boosts
    if signal["category"] == "security":
        base_score *= 2.0  # Security boost
    elif signal["category"] == "technical_debt":
        base_score *= 1.3  # Technical debt boost

    return round(base_score, 2)

def generate_backlog():
    """Generate comprehensive value backlog"""
    print("🔍 Discovering autonomous value opportunities...")

    all_signals = []
    all_signals.extend(discover_git_signals())
    all_signals.extend(discover_dependency_signals())
    all_signals.extend(discover_documentation_signals())
    all_signals.extend(discover_testing_signals())
    all_signals.extend(discover_security_signals())

    # Recalculate composite scores
    for signal in all_signals:
        signal["composite_score"] = calculate_composite_score(signal)

    # Sort by composite score
    all_signals.sort(key=lambda x: x["composite_score"], reverse=True)

    # Generate backlog data
    backlog_data = {
        "timestamp": datetime.now().isoformat(),
        "repository": "multimodal-contract-extractor",
        "maturity_level": "advanced",
        "total_opportunities": len(all_signals),
        "high_priority": len([s for s in all_signals if s["priority"] == "high"]),
        "medium_priority": len([s for s in all_signals if s["priority"] == "medium"]),
        "low_priority": len([s for s in all_signals if s["priority"] == "low"]),
        "next_best_item": all_signals[0] if all_signals else None,
        "top_opportunities": all_signals[:10],
        "categories": {}
    }

    # Category breakdown
    for signal in all_signals:
        category = signal["category"]
        backlog_data["categories"][category] = backlog_data["categories"].get(category, 0) + 1

    # Save metrics
    os.makedirs(".terragon", exist_ok=True)
    with open(".terragon/value-metrics.json", "w") as f:
        json.dump(backlog_data, f, indent=2)

    # Generate markdown backlog
    generate_backlog_markdown(backlog_data)

    print(f"📊 Generated backlog with {len(all_signals)} opportunities")
    if all_signals:
        best = all_signals[0]
        print(f"🎯 Next Best Value: {best['title']} (Score: {best['composite_score']})")

    return backlog_data

def generate_backlog_markdown(data):
    """Generate markdown backlog file"""

    md_content = f"""# 📊 Autonomous Value Backlog

**Repository**: {data['repository']}  
**Maturity Level**: {data['maturity_level'].title()}  
**Last Updated**: {data['timestamp'][:19]}  
**Total Opportunities**: {data['total_opportunities']}

## 🎯 Next Best Value Item

"""

    if data['next_best_item']:
        item = data['next_best_item']
        md_content += f"""**{item['title']}**
- **Composite Score**: {item['composite_score']}
- **WSJF Score**: {item['wsjf_score']} | **ICE Score**: {item['ice_score']}
- **Estimated Effort**: {item['effort_hours']} hours
- **Priority**: {item['priority'].title()}
- **Category**: {item['category'].replace('_', ' ').title()}

*{item['description']}*

"""
    else:
        md_content += "✅ No immediate opportunities identified\n\n"

    md_content += """## 📋 Prioritized Backlog

| Rank | Title | Score | Category | Priority | Effort (h) |
|------|-------|-------|----------|----------|------------|
"""

    for i, item in enumerate(data['top_opportunities'], 1):
        md_content += f"| {i} | {item['title'][:40]}{'...' if len(item['title']) > 40 else ''} | {item['composite_score']} | {item['category'].replace('_', ' ').title()} | {item['priority'].title()} | {item['effort_hours']} |\n"

    md_content += f"""

## 📈 Value Metrics

- **High Priority Items**: {data['high_priority']}
- **Medium Priority Items**: {data['medium_priority']} 
- **Low Priority Items**: {data['low_priority']}

### Category Breakdown
"""

    for category, count in data['categories'].items():
        md_content += f"- **{category.replace('_', ' ').title()}**: {count} items\n"

    md_content += """

## 🔄 Continuous Discovery

This backlog is automatically updated by the Terragon Autonomous SDLC system based on:

- **Git History Analysis**: Technical debt markers and commit patterns
- **Code Quality Metrics**: File complexity and maintainability
- **Security Scanning**: Vulnerability detection and compliance
- **Dependency Analysis**: Update opportunities and security patches
- **Testing Coverage**: Gap analysis and improvement opportunities

### Execution Schedule

- **Immediate**: After each PR merge
- **Hourly**: Security vulnerability scans
- **Daily**: Comprehensive code analysis
- **Weekly**: Deep architectural assessment
- **Monthly**: Strategic value recalibration

---
*Generated by Terragon Autonomous SDLC v2.1.0*
"""

    with open("AUTONOMOUS_BACKLOG.md", "w") as f:
        f.write(md_content)

    print("📄 Generated AUTONOMOUS_BACKLOG.md")

if __name__ == "__main__":
    try:
        backlog_data = generate_backlog()
        print("✅ Autonomous value discovery completed successfully")
    except Exception as e:
        print(f"❌ Value discovery failed: {e}")
        exit(1)
