# snakemake-software-deployment-plugin-container

A generic container plugin implementing snakemake's software-deployment interface.

* It executes the given commands within a rootless container.
* It currently supports both `udocker` and  `podman`.

## Usage

The `kind` parameter specifies valid values for the container runtime to use.

The `container` directive (should be) used to specify the container image to use
for the software deployment. This string should be a valid container image name,
including the tag; e.g., `biocontainers/example:1.0`.

By default, the plugin will attemtp to use 'latest' tag if no tag is provided.
However, be aware that some registries may not support this, for [good
reasons](https://github.com/BioContainers/containers/issues/297#issuecomment-439055879)
having to do with reproducibility. So, it's a good idea to specify a tag.

## Status

- Work in progress. The plugin conforms to the current software-deployment interface specification, and it has passing tests.
- Will revisit when further work is done in snakemake core to allow a more reusable integration of deployment plugins.

## TODO

- [ ] Add support for apptainer
- [ ] Implement repot_sofware method with container URI *and* the resolved hash of the image.
