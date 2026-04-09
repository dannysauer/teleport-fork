# Setting Up Your Own Build Pipeline

This document walks through reproducing the full build pipeline in your own fork.
It assumes you already have a GitHub account and an account on
[build.opensuse.org](https://build.opensuse.org) (OBS).

---

## 1. Fork the repository

Fork `gravitational/teleport` on GitHub.  You will end up with
`github.com/YOU/teleport-fork` (or whatever name you choose).

In your fork's **Settings → General → Default branch**, switch the default
branch from `master` to `autobuild`.

---

## 2. Add the GitHub Actions secret

The only secret the workflows need is an OBS trigger token (created in step 5
below).  Add it as a repository secret named **`OBS_TRIGGER_TOKEN`**:

Settings → Secrets and variables → Actions → New repository secret

---

## 3. Create the OBS project

Log in to [build.opensuse.org](https://build.opensuse.org) and create a new
subproject under your home project, e.g. `home:YOU:teleport`.

### 3a. Set the project config (`prjconf`)

In the OBS web UI, go to your project → **Project Config** tab, and add:

```
PublishFlags: withcontainers
```

This enables OCI container image publishing alongside the RPM/Deb packages.

### 3b. Configure build repositories

Under **Repositories**, add:

| Name | Build against |
|------|---------------|
| `openSUSE_Tumbleweed` | `openSUSE:Factory` standard Tumbleweed repo |
| `Ubuntu_24.04` | `Ubuntu:24.04` standard Ubuntu repo |
| `images` | Your project's own `openSUSE_Tumbleweed` repo (the package built there) |

The `images` repository is where KIWI builds the container; it depends on the
RPM repository so it can install `teleport` into the container image.

---

## 4. Create the `teleport` package in OBS

In your OBS project, create a new package named **`teleport`** and upload every
file from `obs/teleport/` in this repository:

```
obs/teleport/_service
obs/teleport/teleport.spec
obs/teleport/debian/changelog
obs/teleport/debian/compat
obs/teleport/debian/control
obs/teleport/debian/copyright
obs/teleport/debian/rules
```

You can use the OBS web UI (upload files one at a time) or the `osc` CLI:

```bash
osc checkout home:YOU:teleport
cp -r obs/teleport/* home:YOU:teleport/teleport/
cd home:YOU:teleport/teleport
osc addremove
osc commit -m "initial import"
```

> **Note:** The `_service` file references `github.com/YOU/teleport-fork`.
> Update the `<param name="url">` in `obs/teleport/_service` to point to your
> fork before uploading, or edit it directly in the OBS web UI afterward.

---

## 5. Create the `teleport-container` package in OBS

Create a second package named **`teleport-container`** and upload the files from
`obs/teleport-container/`:

```
obs/teleport-container/_service
obs/teleport-container/config.xml
obs/teleport-container/config.sh
```

The container build depends on the `teleport` RPM package being available in
the `openSUSE_Tumbleweed` repository of your project, so the `teleport` package
must build successfully first.

---

## 6. Create an OBS trigger token

OBS trigger tokens let GitHub Actions fire a service re-run on a specific
package without storing your OBS credentials anywhere.

In the OBS web UI, navigate to your project's **teleport** package:

Profile → **Trigger tokens** → New token

- Token type: **Trigger service run**
- Linked package: `home:YOU:teleport / teleport`

Copy the token value and store it as the `OBS_TRIGGER_TOKEN` GitHub secret
(step 2 above).

Repeat for the **`teleport-container`** package — or use the same token if OBS
allows one token to cover multiple packages in the same project.  If not,
create a second token and store it as a separate secret, then update
`prep-obs-source.yml` accordingly.

---

## 7. Update workflow and OBS files with your identifiers

Several files embed `dannysauer` or the full repo path.  Do a search-and-replace
before your first commit:

| File | What to change |
|------|---------------|
| `.github/workflows/sync-registry.yml` | `OBS_IMAGE` env var (OBS project path) |
| `.github/workflows/sync-registry.yml` | `GHCR_IMAGE` env var (if your image name differs) |
| `obs/teleport/_service` | `<param name="url">` — point to your fork |
| `obs/teleport-container/config.xml` | OCI label `org.opencontainers.image.source` |
| `prep-obs-source.yml` | `OBS_PROJECT` variable inside the trigger step |

---

## 8. Set up the `sync-registry.yml` OBS webhook (optional but recommended)

`sync-registry.yml` polls every 15 minutes as a fallback.  For faster
propagation, configure OBS to call the `workflow_dispatch` endpoint when a
container build completes:

1. In OBS, go to your project → **Webhooks** (or package-level notifications).
2. Add a webhook pointing to:
   ```
   https://api.github.com/repos/YOU/teleport-fork/actions/workflows/sync-registry.yml/dispatches
   ```
3. OBS needs a GitHub fine-grained PAT with **Actions: write** permission on
   your repository (read access to the repo is not required).  Store it in OBS
   as the webhook secret/header value.

This is the only credential OBS ever needs; it cannot read your code, push
packages, or perform any other action.

---

## 9. Trigger the first build

Push any commit to the `autobuild` branch (or use **Actions → Run workflow** on
`sync-upstream.yml` to pull the latest upstream tag).  The pipeline will:

1. `sync-upstream.yml` — syncs `master` and pushes the latest upstream tag.
2. `prep-obs-source.yml` — fires on the new tag; builds web assets and
   `fdpass-teleport`; uploads them to the persistent `build-assets` release;
   calls the OBS trigger token.
3. OBS — fetches source via `_service`, vendors Go modules, builds RPM and Deb.
4. OBS — builds the KIWI container image once the RPM is available.
5. `sync-registry.yml` — detects the new image version in OBS and mirrors it
   to `ghcr.io`; packages and pushes Helm charts.

---

## What you still need if you are `dannysauer`

If you have already forked the repo and set the default branch, you only need
to complete steps 4–6 (populate the OBS packages and create the trigger token)
and then add the token as the `OBS_TRIGGER_TOKEN` GitHub secret.  The
workflows and OBS `_service` files already reference the correct repository and
OBS project.

Specifically, upload these files to your existing `home:dannysauer:teleport`
project:

- `obs/teleport/_service`, `teleport.spec`, `debian/` directory → into the
  **`teleport`** package
- `obs/teleport-container/_service`, `config.xml`, `config.sh` → into the
  **`teleport-container`** package

Then create a trigger token (step 6) and add it to GitHub Secrets.  Once those
are in place, run the `sync-upstream.yml` workflow manually to kick off the
first full build.
