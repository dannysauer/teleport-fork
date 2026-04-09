# teleport-fork

Community builds of [Teleport](https://github.com/gravitational/teleport), automatically
kept in sync with upstream and published as installable packages, a container image,
and Helm charts.

> **Source branch:** The `master` branch of this fork is a clean mirror of
> `gravitational/teleport`. This `autobuild` branch contains only the build
> automation — no Teleport source code.

## Packages

### openSUSE Tumbleweed (RPM)

```bash
zypper addrepo https://download.opensuse.org/repositories/home:dannysauer:teleport/openSUSE_Tumbleweed/home:dannysauer:teleport.repo
zypper refresh
zypper install teleport
```

### Ubuntu 24.04 (Deb)

```bash
echo "deb https://download.opensuse.org/repositories/home:dannysauer:teleport/Ubuntu_24.04/ ./" \
  | sudo tee /etc/apt/sources.list.d/teleport.list
curl -fsSL https://download.opensuse.org/repositories/home:dannysauer:teleport/Ubuntu_24.04/Release.key \
  | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/teleport.gpg
sudo apt update
sudo apt install teleport
```

### Container image

```bash
docker pull ghcr.io/dannysauer/teleport:latest
# or pin to a specific version:
docker pull ghcr.io/dannysauer/teleport:19.0.4
```

The image is built on a minimal openSUSE Tumbleweed base and exposes ports
3022–3025 (SSH/tunnel/auth) and 3080 (HTTPS/web UI).

### Helm charts

```bash
# Install teleport-cluster
helm install teleport oci://ghcr.io/dannysauer/charts/teleport-cluster \
  --version 19.0.4 \
  --set clusterName=teleport.example.com

# List available charts
helm search repo oci://ghcr.io/dannysauer/charts
```

Charts are repackaged from upstream with the default image updated to point to
`ghcr.io/dannysauer/teleport`. All other chart values are unchanged from upstream.

## Branch layout

| Branch | Contents |
|--------|----------|
| `autobuild` *(default)* | Build automation, OBS package specs, KIWI container config |
| `master` | Clean mirror of [gravitational/teleport](https://github.com/gravitational/teleport) upstream |

## Automation overview

```mermaid
flowchart TD
    subgraph SRC ["Upstream"]
        upstream(["gravitational/teleport"])
    end

    subgraph GHA ["GitHub Actions"]
        master["master branch"]
        prep["prep-obs-source.yml\nbuild web assets · vendor Rust deps\nupload artifacts · trigger OBS"]
    end

    subgraph OBS ["OBS — home:dannysauer:teleport"]
        obs_pkg["teleport\nRPM + Deb"]
        obs_ctr["teleport-container\nKIWI · Tumbleweed OCI"]
    end

    sync["sync-registry.yml\npull registry.opensuse.org → push ghcr.io\npush Helm charts to ghcr.io OCI"]

    upstream -->|"sync-upstream.yml · every 6h"| master
    master -->|"new tag"| prep
    prep --> obs_pkg & obs_ctr
    obs_pkg & obs_ctr -->|"published · 15 min poll"| sync
```

## Patching upstream

The `patches/` directory holds `.patch` files applied on top of upstream before
building. It is currently empty — these are unmodified upstream builds. See
[patches/README.md](patches/README.md) for how to add patches.

## Reproducing this setup

See [SETUP.md](SETUP.md) for instructions on forking this repository and running
your own equivalent build pipeline.
