# snakemake-software-deployment-plugin-container

A generic container plugin implementing snakemake's software-deployment interface.

* It executes the given commands within a rootless container.
* It currently supports both `udocker` and  `podman`.

## Status

- Work in progress. The plugin conforms to the current software-deployment interface specification, and it has passing tests.
- Will revisit when further work is done in snakemake core to allow a more reusable integration of deployment plugins.


