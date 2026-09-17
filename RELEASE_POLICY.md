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