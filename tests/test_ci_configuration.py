"""Tests for CI/CD pipeline configuration."""

import yaml
from pathlib import Path


class TestCIConfiguration:
    """Test CI/CD pipeline configuration validity."""
    
    def test_github_workflow_syntax(self):
        """Test that GitHub workflow YAML is valid."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "ci.yml"
        
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
        
        # Verify basic structure
        assert "name" in workflow
        assert "on" in workflow  
        assert "jobs" in workflow
        
        # Verify build job exists
        assert "build" in workflow["jobs"]
        build_job = workflow["jobs"]["build"]
        
        assert "runs-on" in build_job
        assert "steps" in build_job
        
    def test_github_actions_versions(self):
        """Test that GitHub Actions use up-to-date versions."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "ci.yml"
        
        with open(workflow_path) as f:
            content = f.read()
        
        # Check for updated action versions
        assert "actions/checkout@v4" in content, "Should use checkout@v4"
        assert "actions/setup-python@v5" in content, "Should use setup-python@v5"
        
        # Ensure old versions are not used
        assert "actions/checkout@v3" not in content, "Should not use outdated checkout@v3"
        assert "actions/setup-python@v4" not in content, "Should not use outdated setup-python@v4"
        
    def test_python_version_specification(self):
        """Test that Python version is properly specified."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "ci.yml"
        
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
        
        build_job = workflow["jobs"]["build"]
        
        # Find setup-python step
        setup_python_step = None
        for step in build_job["steps"]:
            if step.get("uses", "").startswith("actions/setup-python"):
                setup_python_step = step
                break
        
        assert setup_python_step is not None, "Should have setup-python step"
        assert "with" in setup_python_step
        assert "python-version" in setup_python_step["with"]
        
        # Verify Python version is specified
        python_version = setup_python_step["with"]["python-version"]
        assert python_version == "3.12", f"Expected Python 3.12, got {python_version}"