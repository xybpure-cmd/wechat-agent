import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "upload_kb.py"
    spec = importlib.util.spec_from_file_location("upload_kb", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["upload_kb"] = module
    spec.loader.exec_module(module)
    return module


def test_manifest_roundtrip(tmp_path: Path):
    mod = _load_module()
    manifest = tmp_path / "manifest.json"
    tracked = {
        "a.md": mod.TrackedFile(
            path="a.md",
            sha256="hash",
            file_id="file_1",
            vector_store_file_id="vsf_1",
        )
    }

    mod.save_manifest(manifest, tracked)
    loaded = mod.load_manifest(manifest)

    assert loaded["a.md"].sha256 == "hash"
    payload = json.loads(manifest.read_text())
    assert payload["files"]["a.md"]["file_id"] == "file_1"


def test_run_upload_dry_run_incremental(tmp_path: Path, monkeypatch):
    mod = _load_module()
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    a_file = kb_dir / "a.md"
    a_file.write_text("first", encoding="utf-8")

    manifest = tmp_path / "manifest.json"

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("OPENAI_VECTOR_STORE_ID", "vs_test")

    uploaded, unchanged, removed = mod.run_upload(kb_dir=kb_dir, manifest_path=manifest, dry_run=True)
    assert (uploaded, unchanged, removed) == (1, 0, 0)

    digest = mod.sha256_file(a_file)
    mod.save_manifest(
        manifest,
        {
            "a.md": mod.TrackedFile(
                path="a.md",
                sha256=digest,
                file_id="file_1",
                vector_store_file_id="vsf_1",
            )
        },
    )

    uploaded, unchanged, removed = mod.run_upload(kb_dir=kb_dir, manifest_path=manifest, dry_run=True)
    assert (uploaded, unchanged, removed) == (0, 1, 0)
