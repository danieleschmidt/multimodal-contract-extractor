import importlib


def test_web_app_defines_main():
    module = importlib.import_module("web_app")
    assert hasattr(module, "main")
