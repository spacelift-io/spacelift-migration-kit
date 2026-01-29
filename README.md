# Spacelift Migration Kit

This repository holds `spacemk` utility that is responsible for migrating users to Spacelift.
Feel free to open an [issue](https://github.com/spacelift-io/spacelift-migration-kit/issues) on this repository to report bugs or open feature requests.

Please see our documentation [here](https://docs.spacelift.io/product/migrating-to-spacelift) for instructions on using this tool.

## Requirements

- Docker (Docker Desktop, Rancher Desktop, or compatible Docker runtime)

### Rancher Desktop on Apple Silicon

If you're using Rancher Desktop on Apple Silicon (M1/M2/M3), you must enable Rosetta emulation:

```bash
rdctl set --virtual-machine.use-rosetta=true
```

Or enable it via the UI: **Preferences → Virtual Machine → VZ → Enable Rosetta**

This is required because the TFC agent containers run as linux/amd64 and will crash without Rosetta support.
