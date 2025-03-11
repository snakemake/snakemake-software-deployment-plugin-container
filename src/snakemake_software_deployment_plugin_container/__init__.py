__author__ = "ben carrillo"
__copyright__ = "Copyright 2025, ben carrillo"
__email__ = "ben.uzh@pm.me"
__license__ = "MIT"
from dataclasses import dataclass, field
from typing import Iterable, Optional
from snakemake_interface_software_deployment_plugins.settings import (
    SoftwareDeploymentSettingsBase,
)
from snakemake_interface_software_deployment_plugins import (
    EnvBase,
    DeployableEnvBase,
    ArchiveableEnvBase,
    EnvSpecBase,
    SoftwareReport,
)
from shutil import which
from os import getcwd

# Raise errors that will not be handled within this plugin but thrown upwards to
# Snakemake and the user as WorkflowError.
from snakemake_interface_common.exceptions import WorkflowError  # noqa: F401

# The mountpoint for the Snakemake working directory inside the container.
SNAKEMAKE_MOUNTPOINT = "/mnt/snakemake"

UDOCKER = "udocker"
PODMAN = "podman"

# We only support these containers in this plugin for now.
VALID_CONTAINERS = [UDOCKER, PODMAN]

# Optional:
# Define settings for your storage plugin (e.g. host url, credentials).
# They will occur in the Snakemake CLI as --sdm-<plugin-name>-<param-name>
# Make sure that all defined fields are 'Optional' and specify a default value
# of None or anything else that makes sense in your case.
# Note that we allow storage plugin settings to be tagged by the user. That means,
# that each of them can be specified multiple times (an implicit nargs=+), and
# the user can add a tag in front of each value (e.g. tagname1:value1 tagname2:value2).
# This way, a storage plugin can be used multiple times within a workflow with different
# settings.


@dataclass
class ContainerSettings(SoftwareDeploymentSettingsBase):
    kind: Optional[str] = field(
        default="udocker",
        metadata={
            "help": "Container kind (udocker by default)",
            # Optionally request that setting is also available for specification
            # via an environment variable. The variable will be named automatically as
            # SNAKEMAKE_<storage-plugin-name>_<param-name>, all upper case.
            # This mechanism should only be used for passwords, usernames, and other
            # credentials.
            # For other items, we rather recommend to let people use a profile
            # for setting defaults
            # (https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles).
            "env_var": False,
            # Optionally specify a function that parses the value given by the user.
            # This is useful to create complex types from the user input.
            # "parse_func": ...,
            # If a parse_func is specified, you also have to specify an unparse_func
            # that converts the parsed value back to a string.
            # "unparse_func": ...,
            # Optionally specify that setting is required when the executor is in use.
            "required": False,
        },
    )


@dataclass
class ContainerSpec(EnvSpecBase):
    # This class should implement something that describes an existing or to be created
    # environment.
    # It will be automatically added to the environment object when the environment is
    # created or loaded and is available there as attribute self.spec.
    # Use either __init__ with type annotations or dataclass attributes to define the
    # spec.
    # Any attributes that shall hold paths that are interpreted as relative to the
    # workflow source (e.g. the path to an environment definition file), have to be
    # defined as snakemake_interface_software_deployment_plugins.EnvSpecSourceFile.
    # The reason is that Snakemake internally has to convert them from potential
    # URLs or filesystem paths to cached versions.
    # In the Env class below, they have to be accessed as EnvSpecSourceFile.cached
    # (of type Path), when checking for existence. In case errors shall be thrown,
    # the attribute EnvSpecSourceFile.path_or_uri (of type str) can be used to show
    # the original value passed to the EnvSpec.

    # TODO: image_uri should be populated from the container keyword (via whatever mechanism is exposing)
    # the plugin to the software deployment registry.
    image_uri: str

    @classmethod
    def identity_attributes(cls) -> Iterable[str]:
        # Yield the attributes of this subclass that uniquely identify the
        # environment spec. These are used for hashing and equality comparison.
        # For example, the name of the env or the path to the environment definition
        # file or the URI of the container, whatever this plugin uses.

        # TODO: might want to inspect the image and the the hash of the rootfs
        # TODO: for better results, add image_hash
        return ["image_uri"]

    @classmethod
    def source_path_attributes(cls) -> Iterable[str]:
        # Return iterable of attributes of the subclass that represent paths that are
        # supposed to be interpreted as being relative to the defining rule.
        # For example, this would be attributes pointing to conda environment files.
        # Return empty list if no such attributes exist.
        # TODO I *think* source_path to be an abstraction that does not apply to containers
        # but maybe it can be stretched.
        return ()


# Required:
# Implementation of an environment object.
# If your environment cannot be archived or deployed, remove the respective methods
# and the respective base classes.
# All errors should be wrapped with snakemake-interface-common.errors.WorkflowError
class ContainerEnv(EnvBase):
    # TODO: decide if containers are deployable / archivable and add the base images here.
    # does it make sense? Right now I'm not reusing any containers
    # Deployable: can we fetch the image and create a local container?
    # Archiveable: can we export the container to a tarball?
    # , DeployableEnvBase, ArchiveableEnvBase):

    # image_repo is the de-referenced repository from where the image was obtained
    image_repo: str

    # image_hash is a hash of the image that can be used to identify it
    # (TODO: which hash to use, exactly, from the info that we have?)
    image_hash: str

    def __post_init__(self) -> None:
        self.check()

    # The decorator ensures that the decorated method is only called once
    # in case multiple environments of the same kind are created.
    @EnvBase.once
    def check(self) -> None:
        self._check_service()

    def _check_service(self) -> bool:
        if self.spec.image_uri == "":
            raise WorkflowError("Image URI is empty")
        kind = self.settings.kind
        if kind not in VALID_CONTAINERS:
            raise WorkflowError("Invalid container kind")
        if kind == UDOCKER:
            self._check_udocker()
        elif kind == PODMAN:
            self._check_podman()

    def _check_udocker(self):
        if which(UDOCKER) is None:
            raise WorkflowError(f"{UDOCKER} is not available in PATH")
        return True

    def _check_podman(self):
        if which(PODMAN) is None:
            raise WorkflowError(f"{PODMAN} is not available in PATH")
        return True

    def decorate_shellcmd(self, cmd: str) -> str:
        # TODO pass more options here (extra mount volumes, user etc)

        template = (
            "{service} run"
            " --rm"  # Remove container after execution
            " -w {workdir}"  # Working directory inside container
            " -v {hostdir}:{workdir}"  # Mount host directory to container
            " {image_id}"  # Container image
            " {shell}"  # Shell executable
            " -c '{cmd}'"  # The command to execute
        )

        decorated_cmd = template.format(
            service=self.settings.kind,
            workdir=SNAKEMAKE_MOUNTPOINT,
            hostdir=repr(getcwd()),  # TODO: allow to override
            image_id=self.spec.image_uri,
            shell="/bin/sh",
            cmd=cmd.replace("'", r"'\''"),
        )

        return decorated_cmd

    def record_hash(self, hash_object) -> None:
        # Update given hash such that it changes whenever the environment
        # could potentially contain a different set of software (in terms of versions or
        # packages). Use self.spec (containing the corresponding EnvSpec object)
        # to determine the hash.
        # TODO - unsure
        hash_object.update(...)

    def report_software(self) -> Iterable[SoftwareReport]:
        # Report the software contained in the environment. This should be a list of
        # snakemake_interface_software_deployment_plugins.SoftwareReport data class.
        # Use SoftwareReport.is_secondary = True if the software is just some
        # less important technical dependency. This allows Snakemake's report to
        # hide those for clarity. In case of containers, it is also valid to
        # return the container URI as a "software".
        # Return an empty tuple () if no software can be reported.
        # TODO: implement. get container URI + hash
        # Ideally, could peek inside the container to get the installed software (write util that we can
        # use for all container types)
        return ()

    # The methods below are optional. Remove them if not needed and adjust the
    # base classes above.

    async def deploy(self) -> None:
        # Remove method if not deployable!
        # Deploy the environment to self.deployment_path, using self.spec
        # (the EnvSpec object).

        # When issuing shell commands, the environment should use
        # self.run_cmd(cmd: str) -> subprocess.CompletedProcess in order to ensure that
        # it runs within eventual parent environments (e.g. a container or an env
        # module).
        # TODO - implement
        pass

    def is_deployment_path_portable(self) -> bool:
        # Remove method if not deployable!
        # Return True if the deployment is portable, i.e. can be moved to a
        # different location without breaking the environment. Return False otherwise.
        # For example, with conda, environments are not portable in that sense (cannot
        # be moved around, because deployed packages contain hardcoded absolute
        # RPATHs).
        return True

    def remove(self) -> None:
        # Remove method if not deployable!
        # Remove the deployed environment from self.deployment_path and perform
        # any additional cleanup.
        # TODO - remove container?
        pass

    async def archive(self) -> None:
        # Remove method if not archiveable!
        # Archive the environment to self.archive_path.

        # When issuing shell commands, the environment should use
        # self.run_cmd(cmd: str) -> subprocess.CompletedProcess in order to ensure that
        # it runs within eventual parent environments (e.g. a container or an env
        # module).
        # TODO: implement
        # `udocker export <container_id> | tar -'
        pass
