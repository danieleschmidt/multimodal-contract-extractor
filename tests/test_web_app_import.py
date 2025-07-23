import importlib


def test_web_app_defines_main():
    module = importlib.import_module("web_app")
    assert hasattr(module, "main")


def test_temp_file_manager_creates_unique_files():
    """Test that TempFileManager creates unique temporary files."""
    from types import SimpleNamespace
    from web_app import TempFileManager

    upload = SimpleNamespace(name="doc.pdf", read=lambda: b"data")
    
    paths = []
    
    # Create multiple temp files and collect their paths
    for _ in range(2):
        with TempFileManager(upload) as tmp_path:
            paths.append(tmp_path)
            assert tmp_path.exists()
            assert tmp_path.read_bytes() == b"data"
    
    # Verify that different paths were created
    assert paths[0] != paths[1]
    
    # Both files should be cleaned up automatically
    for tmp_path in paths:
        assert not tmp_path.exists()
