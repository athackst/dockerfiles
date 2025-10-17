# Docker Merge Composite Action

Combines per-platform bake metadata into multi-architecture manifests using `docker buildx imagetools create`.

## What It Does
- Gathers bake metadata JSON files (from directories or explicit paths).
- Logs into Docker Hub and/or GHCR when credentials are supplied.
- Creates manifest lists for the requested `family`/`distro` stages, optionally appending an extra tag suffix.
- Outputs the tags that were published so downstream steps can reference them.

## Inputs
| Name | Required | Description |
| --- | --- | --- |
| `family` | ✓ | Image family (folder name). |
| `distro` | ✓ | Release/distro to publish. |
| `metadata` | ✓ | Comma/newline separated list of bake metadata JSON files or directories. |
| `extra-tag` |  | Optional suffix appended to every tag (e.g. a date). |
| `docker-username` / `docker-password` |  | Docker Hub credentials for pushing manifests. |
| `ghcr-username` / `ghcr-password` |  | GHCR credentials for pushing manifests. |
| `dry-run` |  | Set to `true` to print imagetools commands without running them. |

## Outputs
| Name | Description |
| --- | --- |
| `created-tags` | JSON map of manifest stage → list of tags published. |

## Usage
```yaml
- name: Merge manifests
  uses: ./.github/actions/docker-merge
  with:
    family: ros2
    distro: rolling
    metadata: bake-metadata
    ghcr-password: ${{ secrets.GITHUB_TOKEN }}
```

Pair this with the `docker-bake` action: bake on each architecture, upload the metadata artifacts, then run this merge action to publish the multi-architecture tags.
