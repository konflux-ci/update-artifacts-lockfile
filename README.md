# update-artifacts-lockfile

A post-upgrade task script for [MintMaker](https://github.com/konflux-ci/mintmaker) that refreshes checksums in an artifacts lockfile after a dependency version bump.

## What it does

Reads a YAML lockfile containing artifact download URLs and checksums, re-downloads each artifact, recomputes the checksum, and updates the file in place if the checksum has changed.

## Lockfile format

```yaml
artifacts:
  - filename: 'oc'
    download_url: 'https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/4.18.0/openshift-client-linux.tar.gz'
    checksum: 'sha256:abc123...'
```

## Usage

```
update_artifacts_lockfile [path/to/artifacts.lock.yaml]
```

Defaults to `artifacts.lock.yaml` in the current directory if no path is given.

## MintMaker integration

Add to your `renovate.json` `postUpgradeTasks`:

```json
"postUpgradeTasks": {
  "commands": ["update_artifacts_lockfile ci/hermetic/artifacts.lock.yaml"],
  "fileFilters": ["ci/hermetic/artifacts.lock.yaml"],
  "executionMode": "update"
}
```

## Installation

```
pipx install git+https://github.com/konflux-ci/update-artifacts-lockfile.git@v0.1.0
```

## Development

```
uv run --group dev pytest
uv run --group dev ruff check
uv run --group dev mypy src --check-untyped-defs
```
