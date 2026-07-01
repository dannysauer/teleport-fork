# Teleport container OBS package

This KIWI image is built in OBS as:

- Project: `home:dannysauer:teleport`
- Package: `teleport-container`
- Repository: `container`
- Registry image: `registry.opensuse.org/home/dannysauer/teleport/container/dannysauer/teleport:latest`

The `container` repository must include these paths, in this order:

```xml
<path project="home:dannysauer" repository="openSUSE_Slowroll"/>
<path project="home:dannysauer" repository="openSUSE_Factory_ARM"/>
<path project="openSUSE:Tumbleweed" repository="standard"/>
```

`openSUSE_Slowroll` supplies the x86_64 `teleport` RPM. Slowroll does not
publish aarch64 packages, so aarch64 resolves the `teleport` RPM from
`openSUSE_Factory_ARM` and the base image packages from Tumbleweed.

The subproject prjconf must override the inherited container repository build
type so OBS treats `config.kiwi` as a KIWI image description:

```text
Type: kiwi
Repotype: none
Patterntype: none
Prefer: openSUSE-release-appliance-docker
Prefer: openSUSE-release Tumbleweed-release -dummy-release
BuildFlags: logidlelimit:15400
PublishFlags: withcontainers
```
