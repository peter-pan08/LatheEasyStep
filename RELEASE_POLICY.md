# Release Policy

## Branches

`dev` is the complete development branch.

It contains source code, tests, test programs, development documentation,
verification data, measurements and development history.

`main` is the release branch.

It contains only files required for a published LatheEasyStep version,
together with the relevant user documentation.

## Creating a release

A release is created from a tested commit on `dev`.

The program files copied into the release must be identical to the tested
files on `dev`. Creating a release may remove development-only files, but
must not modify the released program code.

The resulting release is added to `main` as one release commit.

Example:

    Release LatheEasyStep 0.8.0
    Release LatheEasyStep 0.9.0
    Release LatheEasyStep 1.0.0

The release commit is tagged with the corresponding version.

## Release history

Development commits remain on `dev` and are not merged into `main`.

`main` therefore contains a compact history of published versions.

Normal merges from `dev` to `main` must not be used for releases.

Likewise, `main` must not be merged back into `dev`.

## Published releases

Published release tags are immutable.

Once a version has been published, its tag and release commit must not be
changed.

Corrections are published as a new patch release.

Example:

    v0.8.0
    v0.8.1
    v0.8.2

## Source traceability

Each release commit should record the exact source commit from `dev` in its
commit message:

    Source-Dev-Commit: <commit SHA>

This allows every release to be traced back to the exact tested development
state.

## Mandatory release procedure

This policy applies to all development environments and all automated or
AI-assisted development tools.

Releases must be created exclusively using the repository release procedure.

Do not merge `dev` into `main`.
Do not merge `main` into `dev`.
Do not manually copy development trees to `main`.
Do not modify an existing published release or release tag.

Before creating a release, read:

- `RELEASE_POLICY.md`
- `release_manifest.txt`

Use:

    python scripts/create_release.py <version>

The release script must not publish or push a release automatically.
The generated release must be reviewed before `main` and the new version tag
are pushed.

The release tree must be created from the exact tested `dev` commit.

`release_manifest.txt` defines the files and directories that belong to a
published release. Only paths listed in this manifest may be included in
`main`.

All listed files must be taken unchanged from the selected `dev` commit.
Development-only files must remain on `dev`.

The release commit must include:

    Source-Dev-Commit: <commit SHA>

These rules are platform-independent and apply equally on Linux, Windows and
other development environments. The tool or agent creating the release is
responsible for following this procedure.

Before publishing, verify that:

1. every path in `release_manifest.txt` exists in the selected `dev` commit;
2. every released file is byte-identical to the corresponding file in that
   `dev` commit;
3. no path outside `release_manifest.txt` is present in the release;
4. `main` contains only the new release commit in addition to previous
   release commits.