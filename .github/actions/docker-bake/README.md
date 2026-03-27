# Docker Bake Composite Action

Builds per-platform images from `templates.yml` using `docker buildx bake`, uploads the resulting metadata, and exposes the release identifiers for follow-up jobs.

## What It Does
- Detects (or accepts) the target platform and computes bake variables for the requested `family` and `distro`.
- Authenticates to Docker Hub and/or GHCR when credentials are supplied.
- Runs `docker/bake-action@v6` to build or push the image targets.
- Reuses BuildKit cache from GHCR when credentials are provided (while still priming the GitHub Actions cache as a fallback).
  - Registry cache export is enabled only when `push=true`.
  - GHA cache behavior is configurable via `gha-cache`:
    - `all`: enable GHA cache import and export
    - `from`: enable only GHA cache import
    - `none`: disable GHA cache import and export
  - GHCR cache/image namespace parts are normalized for valid registry references.
- Persists the bake metadata as an artifact so the merge job can create multi-arch manifests.

## Inputs
| Name | Required | Description |
| --- | --- | --- |
| `family` | ✓ | Repository folder that defines the image family. |
| `distro` | ✓ | Distro/release name (used for Dockerfile and tags). |
| `platform` |  | Override build platform (`os/arch[/variant]`). Defaults to daemon platform. |
| `docker-username` / `docker-password` |  | Docker Hub credentials used for `docker login`. |
| `ghcr-username` / `ghcr-password` |  | GHCR credentials used for `docker login`. |
| `gha-cache` |  | `all` (default), `from`, or `none` for GHA cache mode. |
| `push` |  | Set to `false` to skip pushing digests (defaults to `true`). |

## Outputs
| Name | Description |
| --- | --- |
| `platform` | Canonical build platform used for the bake. |
| `group` | Bake target group (`family-distro-platform`). |
| `release` | Release identifier (`family-distro`). |
| `stage-targets` | JSON array of bake targets that were built. |
| `metadata-path` | Path on disk to the saved bake metadata JSON. |

## Usage
```yaml
- name: Build ROS2 Rolling
  uses: ./.github/actions/docker-bake
  with:
    family: ros2
    distro: rolling
    platform: linux/amd64
    ghcr-username: ${{ github.repository_owner }}
    ghcr-password: ${{ secrets.GITHUB_TOKEN }}
    gha-cache: all
    push: ${{ github.ref == 'refs/heads/main' }}
```

The uploaded `bake-metadata-<group>` artifact and the `metadata-path` output can be consumed by the merge action to publish multi-architecture manifests.
