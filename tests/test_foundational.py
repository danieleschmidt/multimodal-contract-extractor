from pathlib import Path


def test_tests_directory_exists():
    assert Path("tests").is_dir()
    assert Path("tests/__init__.py").is_file()


def test_dummy_success():
    assert True


def test_pytest_config_exists():
    assert Path("pytest.ini").is_file() or Path("pyproject.toml").is_file()
