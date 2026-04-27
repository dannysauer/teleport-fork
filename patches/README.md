# Patches

This directory holds `.patch` files to apply on top of the upstream Teleport
source before building.

## Workflow

Patches are applied in filename sort order (use a numeric prefix to control
ordering, e.g. `0001-my-change.patch`).

They are applied in two places:

1. **`prep-obs-source.yml`** applies them when building web assets and the
   fdpass vendor archive in GitHub Actions (before anything is uploaded to a
   release).
2. **`teleport.spec`** applies them in the `%prep` section before the OBS
   build. List each patch there as:
   ```spec
   Patch0: 0001-my-change.patch
   ...
   %patch -P0 -p1
   ```
3. **`debian/rules`** applies them via `dpkg-source --before-build` if the
   standard quilt workflow is used, or via explicit `patch` calls in
   `override_dh_auto_configure`.

## Generating a patch

```bash
# Start from a clean checkout of master at the target upstream tag
git checkout -b my-feature vX.Y.Z

# Make your changes, then:
git diff vX.Y.Z > patches/0001-describe-the-change.patch
```

## Keeping patches current across upstream updates

When upstream releases a new version, patches may need rebasing:

```bash
git checkout master          # already at new upstream tag after sync
git checkout -b rebase-patches
git am patches/*.patch       # apply in order; resolve conflicts manually
git format-patch vNEW_TAG --output-directory patches/
```

Then commit the updated patches to the `autobuild` branch.
