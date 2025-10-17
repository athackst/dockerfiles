# Docker Targets Composite Action

Produces a list of Docker build targets (family + distro pairs) from `templates.yml`, optionally filtered by platform or changed files.

## What It Does
- Parses `templates.yml` and trims any entries marked as end-of-life.
- Filters results by platform (`os/arch[/variant]`) and/or a list of modified Dockerfiles.
- Returns both the matrix data (`[{family, distro}, …]`) and a deduplicated list of families for downstream jobs.
- Emits a step summary so you can review the generated targets in the workflow UI.

## Inputs
| Name | Required | Description |
| --- | --- | --- |
| `platform` |  | Optional platform filter such as `linux/arm64`. |
| `changed` |  | Comma/newline separated list of Dockerfile paths used to limit the output. |
| `all` |  | Set to `true` to ignore the `changed` filter and return every non-EOL target. |

## Outputs
| Name | Description |
| --- | --- |
| `distros` | JSON array of `{family, distro}` objects suitable for workflow matrices. |
| `families` | JSON array of unique family names. |
| `stages` | JSON array of `{family, distro, stage, platforms}` records for stage-level builds. |

## Usage
```yaml
- name: Discover ROS targets
  id: targets
  uses: ./.github/actions/docker-targets
  with:
    platform: linux/amd64
    changed: ${{ steps.filter.outputs.docker_files }}

- name: Build
  uses: docker/bake-action@v6
  with:
    targets: ${{ fromJSON(steps.targets.outputs.distros)[0].distro }}
```

Fan-out builds or metadata updates by iterating `fromJSON(steps.targets.outputs.distros)` or the simpler `fromJSON(steps.targets.outputs.families)` list when you only need the families. Use `fromJSON(steps.targets.outputs.stages)` when you need stage-level data (stage name + declared platforms) for downstream jobs.
