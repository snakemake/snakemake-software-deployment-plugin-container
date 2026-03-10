import re

__author__ = "ben carrillo"
__copyright__ = "Copyright 2025, ben carrillo"
__email__ = "ben.uzh@pm.me"
__license__ = "MIT"

import os
import shlex
from dataclasses import dataclass, field
from os import getcwd
from shutil import which
from typing import Iterable, List

from snakemake_interface_software_deployment_plugins.settings import (
    SoftwareDeploymentSettingsBase,
    CommonSettings,
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


# ContainerType is an enum that defines the different container types we support.
# If adding new ones, make sure the choice is the same as the command name.
class Runtime(SettingsEnumBase):
    UDOCKER = 0
    PODMAN = 1
    APPTAINER = 2
    DOCKER = 3


@dataclass
class Settings(SoftwareDeploymentSettingsBase):
    runtime: Runtime = field(
        default=Runtime.UDOCKER,
        metadata={
            "help": "Container kind (udocker by default)",
            "env_var": False,
            "required": False,
            "choices": Runtime.choices(),
        },
    )
    mountpoints: List[str] = field(
        default_factory=list,
        metadata={
            "nargs": "+",
            "help": "Additional mount points (format: hostpath:containerpath). "
            "Current working directory and the system tmpdir are always mounted.",
        },
    )
    use_user_namespaces: bool = field(
        default=False,
        metadata={
            "help": "Whether to use user namespaces (if supported by the runtime). "
            "This can be useful to avoid permission issues, but is not always "
            "supported.",
        },
    )


common_settings = CommonSettings(provides="container")


@dataclass(eq=False)
class EnvSpec(EnvSpecBase):
    image_uri: str

    @classmethod
    def identity_attributes(cls) -> Iterable[str]:
        return ["image_uri"]

    @classmethod
    def source_path_attributes(cls) -> Iterable[str]:
        return ()

    def __str__(self) -> str:
        """Return a string representation of the environment spec."""
        return self.image_uri


# All errors should be wrapped with snakemake-interface-common.errors.WorkflowError
class Env(EnvBase):
    # image_repo is the de-referenced repository from where the image was obtained
    image_repo: str
    settings: Settings
    spec: EnvSpec

    # image_hash is a hash of the image that can be used to identify it
    # TODO: populate it *after* fetching/execution
    image_hash: str

    def __post_init__(self) -> None:
        self.check()
        self.runtime_manager = RuntimeManager(self)
        if self.settings.runtime == Runtime.APPTAINER:
            self.runtime_manager = RuntimeManagerApptainer(self)

    # The decorator ensures that the decorated method is only called once
    # in case multiple environments of the same kind are created.
    @EnvBase.once
    def check(self) -> None:
        # TODO: if we don't get the tag, we should assume :latest
        # TODO: normalize tag to always use : instead of # as formerly with singularity
        self._check_service()

    def _check_service(self) -> None:
        # this assumes that the choices are the same as the command names. If
        # this is not the case, we need to add a mapping.
        self._check_executable()

    def _check_executable(self) -> None:
        cmd = self.settings.runtime.item_to_choice()
        if which(cmd) is None:
            raise WorkflowError(f"{cmd} is not available in PATH")

    def decorate_shellcmd(self, cmd: str) -> str:
        return self.runtime_manager.decorate_shellcmd(cmd)

    def contains_executable(self, executable: str) -> bool:
        return (
            self.run_cmd(
                self.decorate_shellcmd(f"which {executable}"),
                check=True,
                capture_output=True,
            ).returncode
            == 0
        )

    def record_hash(self, hash_object) -> None:
        # Update given hash such that it changes whenever the environment
        # could potentially contain a different set of software (in terms of versions or
        # packages). Use self.spec (containing the corresponding EnvSpec object)
        # to determine the hash.
        hash_object.update(self.spec.image_uri.encode())

    def report_software(self) -> Iterable[SoftwareReport]:
        # Report the software contained in the environment. This should be a list of
        # snakemake_interface_software_deployment_plugins.SoftwareReport data class.
        # Use SoftwareReport.is_secondary = True if the software is just some
        # less important technical dependency. This allows Snakemake's report to
        # hide those for clarity. In case of containers, it is also valid to
        # return the container URI as a "software".
        # Return an empty tuple () if no software can be reported.
        return [SoftwareReport(name=self.spec.image_uri)]


@dataclass
class RuntimeManager:
    env: Env

    def options(self) -> str:
        return "--rm"

    def workdir_option(self) -> str:
        return "-w"

    def mount_option(self) -> str:
        return "-v"

    def image_uri(self) -> str:
        return self.env.spec.image_uri

    def subcommand(self) -> str:
        return "run"

    def get_mountpoint_args(self) -> str:
        mountpoint_specs = [
            (self.env.tempdir, self.env.tempdir),
            (getcwd(), getcwd()),
        ] + [(mountpoint, mountpoint) for mountpoint in self.env.mountpoints]

        mountpoints = ""
        # always mount the temporary directory
        for source, mountpoint in mountpoint_specs:
            mountpoints += f" {self.mount_option()} {str(source)!r}:{str(mountpoint)!r}"
        for mountpoint in self.env.settings.mountpoints:
            mountpoints += f" {self.mount_option()} {mountpoint!r}"
        return mountpoints

    # TODO add TEMPDIR env vars, ensure that in addition /tmp is writable
    # in case it is not the same as self.tempdir

    def decorate_shellcmd(self, cmd: str) -> str:
        mountpoints = self.get_mountpoint_args()
        return (
            f"{self.env.settings.runtime} {self.subcommand()}"
            f" {self.options()}"
            f" {self.workdir_option()} {getcwd()!r}"  # Working directory inside container
            f" {mountpoints}"
            f" {self.image_uri()}"  # Container image
            " /bin/sh"  # Shell executable
            f" -c {shlex.quote(cmd)}"  # The command to execute
        )


class RuntimeManagerApptainer(RuntimeManager):
    def subcommand(self) -> str:
        return "exec"

    def options(self) -> str:
        return ""

    def workdir_option(self) -> str:
        return "--cwd"

    def mount_option(self) -> str:
        return "--bind"

    def image_uri(self) -> str:
        if re.match(r"[a-z\.]+://", super().image_uri()):
            return super().image_uri()
        return f"docker://{super().image_uri()}"


class RuntimeManagerDocker(RuntimeManager):
    def options(self) -> str:
        options = super().options()
        if self.env.settings.use_user_namespaces:
            options += " --userns keep-id"
        else:
            uid = os.getuid()
            gid = os.getgid()
            options += f" --user {uid}:{gid}"
        return options
