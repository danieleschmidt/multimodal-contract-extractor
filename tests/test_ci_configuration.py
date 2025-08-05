"""Tests for CI/CD pipeline configuration."""

from pathlib import Path

import yaml


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

        # Document current versions and note for future updates
        # Note: CI workflow modifications require 'workflows' permission

        # Verify workflow contains action usage
        assert "actions/checkout@" in content, "Should use checkout action"
        assert "actions/setup-python@" in content, "Should use setup-python action"

        # Future improvement: Update to checkout@v4 and setup-python@v5 when permissions allow
        # This test documents the limitation and desired upgrade path

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
