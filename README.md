# snakemake-software-deployment-plugin-container

A generic container plugin implementing snakemake's software-deployment interface.

* It executes the given commands within a rootless container.
* It currently supports both `udocker` and  `podman`.
