#!/usr/bin/env python3
"""Upload markdown KB files to OpenAI file search vector store incrementally.

Behavior:
- scans `data/kb/**/*.md`
- computes sha256 per file
- skips unchanged files based on a local manifest
- uploads changed/new files to OpenAI Files API
- attaches uploaded files to a vector store
- removes stale vector-store file entries for deleted local files
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KB_DIR = REPO_ROOT / "data" / "kb"
DEFAULT_MANIFEST = REPO_ROOT / "data" / ".kb_upload_manifest.json"


@dataclass
class TrackedFile:
    path: str
    sha256: str
    file_id: str
    vector_store_file_id: str


def load_dotenv_file() -> None:
    """Load env vars from .env if python-dotenv is available."""
    try:
        from dotenv import load_dotenv

        load_dotenv(REPO_ROOT / ".env")
    except ModuleNotFoundError:
        # Optional dependency at runtime for convenience.
        pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, TrackedFile]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("files", {})
    result: dict[str, TrackedFile] = {}
    for rel_path, item in items.items():
        result[rel_path] = TrackedFile(
            path=rel_path,
            sha256=item["sha256"],
            file_id=item["file_id"],
            vector_store_file_id=item["vector_store_file_id"],
        )
    return result


def save_manifest(path: Path, files: dict[str, TrackedFile]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "files": {
            rel_path: {
                "sha256": tracked.sha256,
                "file_id": tracked.file_id,
                "vector_store_file_id": tracked.vector_store_file_id,
            }
            for rel_path, tracked in sorted(files.items())
        }
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class OpenAIUploader:
    def __init__(self, api_key: str, base_url: str, vector_store_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.vector_store_id = vector_store_id
        import httpx

        self.client = httpx.Client(
            timeout=60,
            headers={
                "Authorization": f"Bearer {api_key}",
            },
        )

    def close(self) -> None:
        self.client.close()

    def upload_file(self, path: Path) -> str:
        with path.open("rb") as f:
            files = {"file": (path.name, f, "text/markdown")}
            data = {"purpose": "assistants"}
            res = self.client.post(f"{self.base_url}/files", files=files, data=data)
        res.raise_for_status()
        return res.json()["id"]

    def attach_to_vector_store(self, file_id: str) -> str:
        res = self.client.post(
            f"{self.base_url}/vector_stores/{self.vector_store_id}/files",
            json={"file_id": file_id},
        )
        res.raise_for_status()
        return res.json()["id"]

    def delete_vector_store_file(self, vector_store_file_id: str) -> None:
        res = self.client.delete(
            f"{self.base_url}/vector_stores/{self.vector_store_id}/files/{vector_store_file_id}"
        )
        if res.status_code not in (200, 404):
            res.raise_for_status()


def resolve_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required env var: {name}")
    return value.strip()


def run_upload(kb_dir: Path, manifest_path: Path, dry_run: bool = False) -> tuple[int, int, int]:
    api_key = resolve_env("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    vector_store_id = resolve_env("OPENAI_VECTOR_STORE_ID")

    tracked = load_manifest(manifest_path)
    current_md_files = sorted(kb_dir.rglob("*.md"))
    current_rel_paths = {str(p.relative_to(kb_dir)) for p in current_md_files}

    removed_paths = sorted(set(tracked.keys()) - current_rel_paths)

    to_upload: list[tuple[Path, str]] = []
    unchanged = 0
    for file_path in current_md_files:
        rel = str(file_path.relative_to(kb_dir))
        digest = sha256_file(file_path)
        old = tracked.get(rel)
        if old and old.sha256 == digest:
            unchanged += 1
            continue
        to_upload.append((file_path, digest))

    print(f"KB dir: {kb_dir}")
    print(f"Found {len(current_md_files)} markdown files")
    print(f"Unchanged: {unchanged}, To upload: {len(to_upload)}, Removed: {len(removed_paths)}")

    if dry_run:
        for file_path, _ in to_upload:
            print(f"[DRY-RUN] upload {file_path}")
        for rel in removed_paths:
            print(f"[DRY-RUN] remove stale {rel}")
        return len(to_upload), unchanged, len(removed_paths)

    uploader = OpenAIUploader(api_key=api_key, base_url=base_url, vector_store_id=vector_store_id)
    try:
        for rel in removed_paths:
            stale = tracked.pop(rel)
            uploader.delete_vector_store_file(stale.vector_store_file_id)
            print(f"Removed stale file mapping: {rel}")

        for file_path, digest in to_upload:
            rel = str(file_path.relative_to(kb_dir))
            old = tracked.get(rel)
            if old:
                uploader.delete_vector_store_file(old.vector_store_file_id)

            file_id = uploader.upload_file(file_path)
            vector_store_file_id = uploader.attach_to_vector_store(file_id)
            tracked[rel] = TrackedFile(
                path=rel,
                sha256=digest,
                file_id=file_id,
                vector_store_file_id=vector_store_file_id,
            )
            print(f"Uploaded: {rel} -> file_id={file_id}, vector_store_file_id={vector_store_file_id}")
    finally:
        uploader.close()

    save_manifest(manifest_path, tracked)
    print(f"Saved manifest: {manifest_path}")
    return len(to_upload), unchanged, len(removed_paths)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Incrementally upload markdown KB to OpenAI vector store")
    parser.add_argument("--kb-dir", default=str(DEFAULT_KB_DIR), help="knowledge base markdown directory")
    parser.add_argument(
        "--manifest",
        default=os.getenv("KB_MANIFEST_PATH", str(DEFAULT_MANIFEST)),
        help="manifest file path",
    )
    parser.add_argument("--dry-run", action="store_true", help="show actions without uploading")
    return parser.parse_args()


def main() -> None:
    load_dotenv_file()
    args = parse_args()
    kb_dir = Path(args.kb_dir).resolve()
    manifest = Path(args.manifest).resolve()
    if not kb_dir.exists():
        raise SystemExit(f"KB directory does not exist: {kb_dir}")

    uploaded, unchanged, removed = run_upload(kb_dir=kb_dir, manifest_path=manifest, dry_run=args.dry_run)
    print(f"Done. uploaded={uploaded}, unchanged={unchanged}, removed={removed}")


if __name__ == "__main__":
    main()
