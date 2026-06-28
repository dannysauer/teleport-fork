# Patches

This directory holds `.patch` files to apply on top of the upstream Teleport
source before building.

## Workflow

Patches are applied in filename sort order (use a numeric prefix to control
ordering, e.g. `0001-my-change.patch`).

They are applied in these places:

1. **`prep-obs-source.yml`** applies every `*.patch` from this directory before
   building web assets, `fdpass-teleport`, and the fdpass vendor archive in
   GitHub Actions.
2. **`teleport.spec`** applies every `*.patch` found in the OBS source
   directory during `%prep`.
3. **`debian/rules`** applies every `*.patch` found beside the unpacked source
   during `override_dh_auto_configure`.

Do not add individual `Patch0` or `%patch` entries to the spec. Add or remove
patch files in this directory and let the sorted filename order define the
application order.

## Generating a patch

```bash
# Start from a worktree that has both master and autobuild.
git switch autobuild
git switch -c my-feature
git worktree add /tmp/teleport-upstream vX.Y.Z

# Make your changes in /tmp/teleport-upstream, then from this branch:
git -C /tmp/teleport-upstream diff vX.Y.Z > patches/0001-describe-the-change.patch
```

## Keeping patches current across upstream updates

When upstream releases a new version, patches may need rebasing:

```bash
git switch autobuild
git switch -c rebase-patches
git worktree add /tmp/teleport-rebase vNEW_TAG
for p in patches/*.patch; do git -C /tmp/teleport-rebase apply "$PWD/$p"; done
# Resolve conflicts manually, then regenerate raw diff patches as needed.
git -C /tmp/teleport-rebase diff vNEW_TAG > patches/0001-describe-the-change.patch
```

Then commit the updated patches to the `autobuild` branch.
