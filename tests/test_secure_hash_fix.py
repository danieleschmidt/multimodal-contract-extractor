"""Test secure hash implementation for cache keys."""

from PIL import Image

from multimodal_contract_extractor.clause_detection import _hash_image


def test_hash_image_consistency():
    """Test that image hashing produces consistent results."""
    # Create a simple test image
    image = Image.new("RGB", (100, 100), color="red")

    # Hash should be consistent
    hash1 = _hash_image(image)
    hash2 = _hash_image(image)

    assert hash1 == hash2, "Hash should be consistent for same image"
    assert isinstance(hash1, str), "Hash should be a string"
    assert len(hash1) > 0, "Hash should not be empty"


def test_hash_image_different_for_different_images():
    """Test that different images produce different hashes."""
    image1 = Image.new("RGB", (100, 100), color="red")
    image2 = Image.new("RGB", (100, 100), color="blue")

    hash1 = _hash_image(image1)
    hash2 = _hash_image(image2)

    assert hash1 != hash2, "Different images should produce different hashes"


def test_hash_algorithm_is_secure():
    """Test that the hash algorithm is cryptographically secure."""
    image = Image.new("RGB", (100, 100), color="red")
    hash_result = _hash_image(image)

    # SHA-256 produces 64-character hex strings (32 bytes * 2)
    assert len(hash_result) == 64, f"Expected SHA-256 hash length 64, got {len(hash_result)}"

    # Verify it's a valid hex string
    int(hash_result, 16)  # Should not raise an exception

    # Verify we're not using MD5 (which produces 32-character hex strings)
    assert len(hash_result) != 32, "Should not be using MD5 (32-character hash)"
