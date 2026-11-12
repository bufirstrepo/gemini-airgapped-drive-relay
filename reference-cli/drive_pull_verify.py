#!/usr/bin/env python3
"""Reference local verifier for Air-Gapped Cloud-Drive Relay staging bundles.

Validates that a staged folder pulled from Google Drive satisfies strict local
safety invariants before a developer executes code with @google/gemini-cli:
  1. Confirms gVisor runtime attestation and inbound_tunnel_open=false.
  2. Blocks path traversal ('..', absolute paths, backslashes, and symlinks).
  3. Verifies SHA-256 digests and exact byte lengths for every staged file.
  4. Flags build/hook files that require human diff review before execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile

SENSITIVE_BUILD_PATTERNS = (
    "Makefile",
    "CMakeLists.txt",
    "package.json",
    "pyproject.toml",
    ".csproj",
    ".sh",
    ".ps1",
    ".bat",
    ".github/workflows/",
)

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class BundleVerificationError(Exception):
    """Raised when a staged bundle violates security or integrity invariants."""


def is_safe_relative_path(rel_path: str) -> bool:
    """Reject absolute paths, parent traversal, backslashes, and empty paths."""
    if not rel_path or "\\" in rel_path:
        return False
    pure = pathlib.PurePosixPath(rel_path)
    if pure.is_absolute():
        return False
    if any(part in ("..", ".", "") for part in pure.parts):
        return False
    return True


def validate_manifest_structure(manifest: dict) -> list[str]:
    """Validate manifest fields and return any build-script review notices."""
    if manifest.get("manifest_version") != "1.0.0":
        raise BundleVerificationError("Unsupported manifest_version.")

    attestation = manifest.get("sandbox_attestation", {})
    if attestation.get("runtime") != "gvisor-runsc":
        raise BundleVerificationError("Untrusted sandbox runtime in attestation.")
    if attestation.get("inbound_tunnel_open") is not False:
        raise BundleVerificationError("Attestation failed: inbound_tunnel_open must be false.")

    origin = manifest.get("origin_plane", {})
    if origin.get("drive_scope") != "https://www.googleapis.com/auth/drive.file":
        raise BundleVerificationError("Unexpected OAuth scope; expected narrow drive.file scope.")

    files = manifest.get("files", [])
    if not isinstance(files, list) or not files:
        raise BundleVerificationError("Manifest contains no file entries.")

    notices: list[str] = []
    seen_paths: set[str] = set()

    for entry in files:
        rel_path = entry.get("relative_path", "")
        if not is_safe_relative_path(rel_path):
            raise BundleVerificationError(f"Unsafe relative_path rejected: {rel_path!r}")
        if rel_path in seen_paths:
            raise BundleVerificationError(f"Duplicate file entry rejected: {rel_path}")
        seen_paths.add(rel_path)

        digest = entry.get("sha256", "")
        if not SHA256_RE.match(digest):
            raise BundleVerificationError(f"Invalid SHA-256 format for {rel_path}")

        size_bytes = entry.get("size_bytes", -1)
        if not isinstance(size_bytes, int) or size_bytes < 0:
            raise BundleVerificationError(f"Invalid size_bytes for {rel_path}")

        if entry.get("executable_warning") or any(p in rel_path for p in SENSITIVE_BUILD_PATTERNS):
            notices.append(f"REVIEW REQUIRED before local CLI execution: {rel_path}")

    return notices


def verify_staged_directory(manifest: dict, staging_dir: pathlib.Path) -> None:
    """Verify on-disk files match SHA-256 digests and contain no symlinks."""
    root = staging_dir.resolve()
    for entry in manifest["files"]:
        rel_path = entry["relative_path"]
        target = root / rel_path

        if target.is_symlink():
            raise BundleVerificationError(f"Symlink rejected in staging tree: {rel_path}")

        resolved = target.resolve()
        if not str(resolved).startswith(str(root) + os.sep):
            raise BundleVerificationError(f"Path escaped staging root: {rel_path}")

        if not resolved.is_file():
            raise BundleVerificationError(f"Missing expected file: {rel_path}")

        actual_bytes = resolved.read_bytes()
        if len(actual_bytes) != entry["size_bytes"]:
            raise BundleVerificationError(
                f"Size mismatch on {rel_path}: expected {entry['size_bytes']}, got {len(actual_bytes)}"
            )

        actual_hash = hashlib.sha256(actual_bytes).hexdigest()
        if actual_hash != entry["sha256"]:
            raise BundleVerificationError(
                f"SHA-256 mismatch on {rel_path}: expected {entry['sha256']}, got {actual_hash}"
            )

        # Strip execute bits on staged files by default for passive handoff safety
        os.chmod(resolved, 0o644)


def run_self_test() -> int:
    """Execute built-in unit checks for manifest, hash, and path-traversal guards."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        plan_text = b"# Plan\nSafe cloud build artifact.\n"
        plan_file = tmp_path / "implementation_plan.md"
        plan_file.write_bytes(plan_text)
        os.chmod(plan_file, 0o755)  # Intentionally executable to verify chmod 0644 strip

        valid_manifest = {
            "manifest_version": "1.0.0",
            "run_id": "self_test_20261111",
            "created_utc": "2026-11-11T22:45:00Z",
            "origin_plane": {
                "trigger": "gemini-live-voice",
                "engine": "antigravity-2.0-worker",
                "drive_scope": "https://www.googleapis.com/auth/drive.file",
            },
            "sandbox_attestation": {
                "runtime": "gvisor-runsc",
                "network_egress_policy": "allowlist-only",
                "inbound_tunnel_open": False,
            },
            "artifacts": {
                "implementation_plan": "implementation_plan.md",
                "test_summary": {"passed": 12, "failed": 0, "duration_ms": 420},
            },
            "files": [
                {
                    "relative_path": "implementation_plan.md",
                    "sha256": hashlib.sha256(plan_text).hexdigest(),
                    "size_bytes": len(plan_text),
                    "executable_warning": False,
                }
            ],
        }

        validate_manifest_structure(valid_manifest)
        verify_staged_directory(valid_manifest, tmp_path)

        mode = plan_file.stat().st_mode & 0o777
        assert mode == 0o644, f"Expected 0644 permissions, got {oct(mode)}"

        # Confirm path traversal is blocked
        bad_manifest = json.loads(json.dumps(valid_manifest))
        bad_manifest["files"][0]["relative_path"] = "../../etc/passwd"
        try:
            validate_manifest_structure(bad_manifest)
            raise AssertionError("Traversal path was not rejected!")
        except BundleVerificationError:
            pass

    print("[PASS] Air-Gapped Drive Relay integrity and path-traversal checks succeeded.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an Air-Gapped Cloud-Drive Relay bundle.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in verification test suite.")
    parser.add_argument("--manifest", type=pathlib.Path, help="Path to artifact-manifest.json.")
    parser.add_argument("--staging-dir", type=pathlib.Path, help="Path to pulled staging directory.")
    parser.add_argument("--dry-run", action="store_true", help="Validate manifest structure without checking disk files.")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if not args.manifest:
        parser.error("Provide --manifest or run --self-test.")

    manifest_data = json.loads(args.manifest.read_text(encoding="utf-8"))
    notices = validate_manifest_structure(manifest_data)
    print(f"[OK] Manifest structure valid for run_id={manifest_data['run_id']}")

    if not args.dry_run:
        if not args.staging_dir:
            parser.error("Provide --staging-dir unless --dry-run is set.")
        verify_staged_directory(manifest_data, args.staging_dir)
        print(f"[OK] Verified {len(manifest_data['files'])} file(s) in {args.staging_dir}")

    for notice in notices:
        print(f"[NOTICE] {notice}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
