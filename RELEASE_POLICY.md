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

## Documentation-only corrections

This is a narrow, explicit exception to "Mandatory release procedure"
below, not a second release mechanism. It does not use
`scripts/create_release.py` and does not produce a release.

Release-line documentation can contain mistakes that have nothing to do
with the released program (for example a notice about the repository
itself). Fixing such a mistake must not require publishing the current
`dev` program state as a release.

A documentation-only correction is a single commit added directly on top
of the current `main` tip. It:

- receives no version number and no tag - it is not a release;
- must not contain any runtime or program file (anything under
  `lathe_easystep/`, `lathe_easystep.ui`, `lathe_easystep_handler.py`, or
  any other file that ships program behavior);
- may only touch paths from this explicit allowlist:

      README.md

  This list may only be extended with genuinely non-behavioral
  documentation files, never with program files.
- does not require a `Source-Dev-Commit:` trailer (see "Source
  traceability") - that marker identifies a program state derived from
  `dev`, which a documentation-only correction is not;
- uses a commit message starting with `Documentation correction:` rather
  than `Release LatheEasyStep`, so it is never mistaken for a release in
  `main`'s history.

Before publishing a documentation-only correction, it must be verified
that the commit changes nothing except the allowed path(s) compared to
the previous `main`, for example:

    git diff --name-only <previous-main-commit> <new-commit>

The result must be exactly the allowed path(s) - nothing else.

Normal corrections to the released program remain patch releases created
through `scripts/create_release.py`, exactly as described above. This
exception does not replace that procedure for anything outside the
allowlist.

A later regular release may be created directly on top of a
documentation-only correction commit without any special handling:
`scripts/create_release.py` replaces the entire release tree from
`release_manifest.txt` against the chosen `dev` commit regardless of what
the current `main` tip contains, so the next real release simply
supersedes the correction.

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
   release commits and any permitted documentation-only correction
   commits (see "Documentation-only corrections").
