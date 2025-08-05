"""Tests for security dependency version requirements."""

import pkg_resources
import pytest


class TestSecurityDependencies:
    """Test that security-critical dependencies meet minimum version requirements."""

    def test_cryptography_version_security_requirement(self):
        """Test that cryptography is at least version 45.0.0 for security fixes."""
        try:
            pkg_resources.require("cryptography>=45.0.0")
        except pkg_resources.DistributionNotFound:
            pytest.skip("cryptography not installed")
        except pkg_resources.VersionConflict as e:
            pytest.fail(f"cryptography version too old for security requirements: {e}")

    def test_defusedxml_version_requirement(self):
        """Test that defusedxml is at required version for XML security."""
        try:
            pkg_resources.require("defusedxml>=0.7")
        except pkg_resources.DistributionNotFound:
            pytest.skip("defusedxml not installed")
        except pkg_resources.VersionConflict as e:
            pytest.fail(f"defusedxml version too old: {e}")

    def test_pillow_version_requirement(self):
        """Test that Pillow is at required version for image security."""
        try:
            pkg_resources.require("Pillow>=10")
        except pkg_resources.DistributionNotFound:
            pytest.skip("Pillow not installed")
        except pkg_resources.VersionConflict as e:
            pytest.fail(f"Pillow version too old: {e}")
