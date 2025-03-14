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
    EnvSpecBase,
    SoftwareReport,
)

# Raise errors that will not be handled within this plugin but thrown upwards to
# Snakemake and the user as WorkflowError.
from snakemake_interface_common.exceptions import WorkflowError  # noqa: F401
from snakemake_interface_common.settings import SettingsEnumBase

from shutil import which
from os import getcwd


# The mountpoint for the Snakemake working directory inside the container.
SNAKEMAKE_MOUNTPOINT = "/mnt/snakemake"


# ContainerType is an enum that defines the different container types we support.
# If adding new ones, make sure the choice is the same as the command name.
class ContainerType(SettingsEnumBase):
    UDOCKER = 0
    PODMAN = 1


@dataclass
class ContainerSettings(SoftwareDeploymentSettingsBase):
    kind: Optional[ContainerType] = field(
        default=ContainerType.UDOCKER,
        metadata={
            "help": "Container kind (udocker by default)",
            "env_var": False,
            "required": False,
        },
    )


@dataclass
class ContainerSpec(EnvSpecBase):
    # TODO: when integrating this plugin, image_uri should be populated from the container keyword (via whatever mechanism is exposing)
    # the plugin to the software deployment registry.
    image_uri: str

    @classmethod
    def identity_attributes(cls) -> Iterable[str]:
        return ["image_uri"]

    @classmethod
    def source_path_attributes(cls) -> Iterable[str]:
        return ()


# All errors should be wrapped with snakemake-interface-common.errors.WorkflowError
class ContainerEnv(EnvBase):
    # image_repo is the de-referenced repository from where the image was obtained
    image_repo: str

    # image_hash is a hash of the image that can be used to identify it
    # TODO: populate it *after* fetching/execution
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

        # TODO: if we don't get the tag, we should assume :latest

        if self.settings.kind not in ContainerType.all():
            raise WorkflowError("Invalid container kind")

        # this assumes that the choices are the same as the command names. If
        # this is not the case, we need to add a mapping.
        self._check_executable()

    def _check_executable(self):
        cmd = self.settings.kind.item_to_choice()
        if which(cmd) is None:
            raise WorkflowError(f"{cmd} is not available in PATH")
        return True

    def decorate_shellcmd(self, cmd: str) -> str:
        # TODO pass more options here (extra mount volumes, user etc)
        # TODO need to mount .cache too

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
        hash_object.update(...)

    def report_software(self) -> Iterable[SoftwareReport]:
        # Report the software contained in the environment. This should be a list of
        # snakemake_interface_software_deployment_plugins.SoftwareReport data class.
        # Use SoftwareReport.is_secondary = True if the software is just some
        # less important technical dependency. This allows Snakemake's report to
        # hide those for clarity. In case of containers, it is also valid to
        # return the container URI as a "software".
        # Return an empty tuple () if no software can be reported.
        # TODO: implement.
        # Get container URI + hash (assuming we've already executd and fetched the image,
        # so that we can get the hash for the image plus the tag)
        return ()
