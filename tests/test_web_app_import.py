import importlib
from pathlib import Path


def test_web_app_defines_main():
    module = importlib.import_module("web_app")
    assert hasattr(module, "main")

def test_save_uploaded_file_unique(tmp_path, monkeypatch):
    import tempfile
    from types import SimpleNamespace

    import web_app

    created = []

    real_tempfile = tempfile.NamedTemporaryFile

    def fake_named_tempfile(*args, **kwargs):
        tmp = real_tempfile(delete=False, dir=tmp_path, suffix=kwargs.get("suffix", ""))
        created.append(Path(tmp.name))
        return tmp

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", fake_named_tempfile)

    upload = SimpleNamespace(name="doc.pdf", read=lambda: b"data")
    path1 = web_app.save_upload(upload)
    path2 = web_app.save_upload(upload)

    assert path1 != path2
    assert path1.exists()
    assert path2.exists()

    for p in created:
        p.unlink()
