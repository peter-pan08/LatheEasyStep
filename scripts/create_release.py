#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


class ReleaseError(RuntimeError):
    pass


def run_git(
    repo: Path,
    *args: str,
    cwd: Path | None = None,
    check: bool = True,
) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd or repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise ReleaseError(
            f"git {' '.join(args)} failed:\n{message}"
        )

    return result.stdout.strip()


def git_ok(repo: Path, *args: str) -> bool:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        raise ReleaseError("Not inside a Git repository.")

    return Path(result.stdout.strip()).resolve()


def read_manifest(repo: Path) -> list[str]:
    manifest = repo / "release_manifest.txt"

    if not manifest.is_file():
        raise ReleaseError("release_manifest.txt not found.")

    entries: list[str] = []

    for raw_line in manifest.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("/") or line.startswith("\\"):
            raise ReleaseError(
                f"Manifest entry must be repository-relative: {line}"
            )

        normalized = line.replace("\\", "/")

        if ".." in Path(normalized).parts:
            raise ReleaseError(
                f"Manifest entry may not contain '..': {line}"
            )

        entries.append(normalized)

    if not entries:
        raise ReleaseError("release_manifest.txt is empty.")

    if len(entries) != len(set(entries)):
        raise ReleaseError("release_manifest.txt contains duplicate entries.")

    return entries


def require_clean_worktree(repo: Path) -> None:
    status = run_git(
        repo,
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    if status:
        raise ReleaseError(
            "Working tree is not clean.\n"
            "Commit or discard all changes before creating a release:\n"
            + status
        )

    unexpected: list[str] = []

    for line in status.splitlines():
        if not line:
            continue

        path = line[3:].strip()

        if " -> " in path:
            path = path.split(" -> ", 1)[1]

        path = path.strip('"').replace("\\", "/")

        if path not in allowed:
            unexpected.append(line)

    if unexpected:
        raise ReleaseError(
            "Working tree contains unrelated changes:\n"
            + "\n".join(unexpected)
        )


def resolve_source_commit(repo: Path, source_ref: str) -> str:
    if not git_ok(repo, "rev-parse", "--verify", f"{source_ref}^{{commit}}"):
        raise ReleaseError(
            f"Source ref does not resolve to a commit: {source_ref}"
        )

    source = run_git(
        repo,
        "rev-parse",
        f"{source_ref}^{{commit}}",
    )

    if not git_ok(repo, "merge-base", "--is-ancestor", source, "dev"):
        raise ReleaseError(
            f"Source commit {source} is not contained in local dev."
        )

    return source


def require_main(repo: Path) -> str:
    if not git_ok(repo, "rev-parse", "--verify", "main^{commit}"):
        raise ReleaseError("Local main branch does not exist.")

    return run_git(repo, "rev-parse", "main^{commit}")


def require_synced_refs(repo: Path, source: str, main_commit: str) -> None:
    if not git_ok(repo, "rev-parse", "--verify", "origin/dev^{commit}"):
        raise ReleaseError(
            "origin/dev is unavailable. Run 'git fetch origin' first."
        )

    if not git_ok(repo, "rev-parse", "--verify", "origin/main^{commit}"):
        raise ReleaseError(
            "origin/main is unavailable. Run 'git fetch origin' first."
        )

    origin_dev = run_git(repo, "rev-parse", "origin/dev^{commit}")
    origin_main = run_git(repo, "rev-parse", "origin/main^{commit}")

    if source != origin_dev:
        raise ReleaseError(
            "Selected source commit is not the current origin/dev.\n"
            f"Source:     {source}\n"
            f"origin/dev: {origin_dev}"
        )

    if main_commit != origin_main:
        raise ReleaseError(
            "Local main is not identical to origin/main.\n"
            f"main:        {main_commit}\n"
            f"origin/main: {origin_main}"
        )


def require_new_version(repo: Path, version: str) -> str:
    if not VERSION_RE.fullmatch(version):
        raise ReleaseError(
            "Version must use x.y.z format, for example 0.9.0."
        )

    tag = f"v{version}"

    if git_ok(repo, "rev-parse", "--verify", f"refs/tags/{tag}"):
        raise ReleaseError(f"Tag already exists locally: {tag}")

    remote = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--tags", "origin", f"refs/tags/{tag}"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if remote.returncode == 0:
        raise ReleaseError(f"Tag already exists on origin: {tag}")

    if remote.returncode not in (0, 2):
        message = remote.stderr.strip() or remote.stdout.strip()
        raise ReleaseError(
            "Unable to check remote release tag:\n" + message
        )

    return tag


def manifest_files(
    repo: Path,
    source: str,
    entries: list[str],
) -> list[str]:
    all_files = run_git(
        repo,
        "ls-tree",
        "-r",
        "--name-only",
        source,
    ).splitlines()

    all_files_set = set(all_files)
    selected: set[str] = set()

    for entry in entries:
        if entry.endswith("/"):
            prefix = entry
            matches = {
                path for path in all_files
                if path.startswith(prefix)
            }

            if not matches:
                raise ReleaseError(
                    f"Manifest directory does not exist or is empty "
                    f"in source commit: {entry}"
                )

            selected.update(matches)

        else:
            if entry not in all_files_set:
                raise ReleaseError(
                    f"Manifest file does not exist in source commit: {entry}"
                )

            selected.add(entry)

    return sorted(selected)


def check_manifest_current_files(
    repo: Path,
    entries: list[str],
) -> None:
    # Make sure release-control files cannot accidentally enter main.
    forbidden = {
        "RELEASE_POLICY.md",
        "release_manifest.txt",
        "scripts/create_release.py",
    }

    for entry in entries:
        normalized = entry.rstrip("/")

        if normalized in forbidden:
            raise ReleaseError(
                f"Development-only release control file is present "
                f"in release_manifest.txt: {entry}"
            )


def create_release_commit(
    repo: Path,
    version: str,
    source: str,
    expected_files: list[str],
) -> tuple[str, Path]:
    temp_root = Path(
        tempfile.mkdtemp(prefix="lathe-easystep-release-")
    ).resolve()

    worktree = temp_root / "main"

    try:
        run_git(
            repo,
            "worktree",
            "add",
            "--detach",
            str(worktree),
            "main",
        )

        # Remove the complete previous release tree from the index/worktree.
        run_git(
            repo,
            "rm",
            "-r",
            "--ignore-unmatch",
            ".",
            cwd=worktree,
        )

        # Restore exactly the manifest-selected files from the tested source.
        for path in expected_files:
            run_git(
                repo,
                "restore",
                f"--source={source}",
                "--staged",
                "--worktree",
                "--",
                path,
                cwd=worktree,
            )

        message = (
            f"Release LatheEasyStep {version}\n\n"
            f"Source-Dev-Commit: {source}"
        )

        run_git(
            repo,
            "commit",
            "-m",
            message,
            cwd=worktree,
        )

        release_commit = run_git(
            repo,
            "rev-parse",
            "HEAD",
            cwd=worktree,
        )

        verify_release(
            repo,
            source,
            release_commit,
            expected_files,
        )

        # Move main only after all verification succeeded.
        run_git(
            repo,
            "branch",
            "-f",
            "main",
            release_commit,
        )

        return release_commit, worktree

    except Exception:
        try:
            run_git(
                repo,
                "worktree",
                "remove",
                "--force",
                str(worktree),
                check=False,
            )
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)
        raise


def verify_release(
    repo: Path,
    source: str,
    release: str,
    expected_files: list[str],
) -> None:
    release_files = run_git(
        repo,
        "ls-tree",
        "-r",
        "--name-only",
        release,
    ).splitlines()

    expected = set(expected_files)
    actual = set(release_files)

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)

    if missing:
        raise ReleaseError(
            "Release is missing manifest files:\n"
            + "\n".join(missing)
        )

    if extra:
        raise ReleaseError(
            "Release contains files outside release_manifest.txt:\n"
            + "\n".join(extra)
        )

    for path in expected_files:
        source_blob = run_git(
            repo,
            "rev-parse",
            f"{source}:{path}",
        )

        release_blob = run_git(
            repo,
            "rev-parse",
            f"{release}:{path}",
        )

        if source_blob != release_blob:
            raise ReleaseError(
                f"Released file differs from source commit: {path}"
            )

    parents = run_git(
        repo,
        "rev-list",
        "--parents",
        "-n",
        "1",
        release,
    ).split()

    if len(parents) != 2:
        raise ReleaseError(
            "Release commit must have exactly one parent."
        )

    previous_main = run_git(repo, "rev-parse", "main^{commit}")

    if parents[1] != previous_main:
        raise ReleaseError(
            "Release commit is not a direct child of current main."
        )


def cleanup_worktree(repo: Path, worktree: Path) -> None:
    temp_root = worktree.parent

    run_git(
        repo,
        "worktree",
        "remove",
        "--force",
        str(worktree),
        check=False,
    )

    shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a LatheEasyStep release from dev."
    )

    parser.add_argument(
        "version",
        help="Release version in x.y.z format, for example 0.9.0",
    )

    parser.add_argument(
        "--source",
        default="dev",
        help="Source ref on dev (default: dev)",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the release prerequisites without changing anything",
    )

    args = parser.parse_args()

    try:
        repo = repository_root()

        if shutil.which("git") is None:
            raise ReleaseError("git executable not found.")

        entries = read_manifest(repo)
        check_manifest_current_files(repo, entries)

        require_clean_worktree(repo)

        source = resolve_source_commit(repo, args.source)
        main_commit = require_main(repo)

        require_synced_refs(repo, source, main_commit)

        tag = require_new_version(repo, args.version)

        expected_files = manifest_files(
            repo,
            source,
            entries,
        )

        print(f"Repository:        {repo}")
        print(f"Version:           {args.version}")
        print(f"Tag:               {tag}")
        print(f"Source dev commit: {source}")
        print(f"Current main:      {main_commit}")
        print(f"Release files:     {len(expected_files)}")

        if args.check:
            print()
            print("CHECK OK - no repository changes were made.")
            return 0

        release_commit, worktree = create_release_commit(
            repo,
            args.version,
            source,
            expected_files,
        )

        cleanup_worktree(repo, worktree)

        print()
        print("RELEASE PREPARED AND VERIFIED")
        print(f"Release commit:    {release_commit}")
        print(f"Source dev commit: {source}")
        print()
        print("Nothing has been pushed and no tag has been created.")
        print()
        print("After manual review, publish with:")
        print(f"  git tag {tag} {release_commit}")
        print("  git push origin main")
        print(f"  git push origin {tag}")

        return 0

    except ReleaseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())