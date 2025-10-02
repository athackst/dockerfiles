# 🚀 Docker Build & Push (Local Action)

Local composite GitHub Action for building & pushing Docker images to **Docker Hub** + **GHCR** with caching and multi-platform support.

## 📥 Inputs
- `label` (dir with Dockerfile)  
- `tag` (Dockerfile/tag name)  
- `target` (build stage)  
- `platforms` (e.g. `linux/amd64,linux/arm64`)  

## 🔑 Secrets/Vars
- `DOCKERHUB_USERNAME` (var)  
- `DOCKERHUB_PASSWORD` (secret)  
- `GITHUB_TOKEN` (auto, needs `packages: write`)  

## 🖥 Example
```yaml
- uses: ./.github/actions/docker-build-push
  with:
    label: foo
    tag: base
    target: runtime
    platforms: linux/amd64,linux/arm64
```

## 🏷 Tags
- DockerHub: `${DOCKERHUB_USERNAME}/${label}:${tag}-${target}[-date]`  
- GHCR: `ghcr.io/${GITHUB_REPOSITORY_OWNER}/${label}:${tag}-${target}`
