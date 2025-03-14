__author__ = "ben carrillo"
__copyright__ = "Copyright 2025, ben carrillo"
__email__ = "ben.uzh@pm.me"
__license__ = "MIT"
import json
import os.path
import subprocess
import tempfile

from dataclasses import dataclass, field
from os import getcwd
from shutil import which
from typing import Iterable, Optional

from snakemake.common import get_appdirs
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


# The mountpoint for the Snakemake working directory inside the container.
SNAKEMAKE_MOUNTPOINT = "/mnt/snakemake"

# Where the source-cache dir is found under the cache folder
SOURCE_CACHE = "snakemake/source-cache"


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

    def _get_image_uri_and_tag(self) -> Iterable[str]:
        parts = self.spec.image_uri.split(":")
        if len(parts) > 2:
            raise WorkflowError("Malformed image URI", self.spec.image_uri)
        if len(parts) != 2:
            parts += ["latest"]
        return parts

    # The decorator ensures that the decorated method is only called once
    # in case multiple environments of the same kind are created.
    @EnvBase.once
    def check(self) -> None:
        self._check_service()

    def _check_service(self) -> bool:
        if self.spec.image_uri == "":
            raise WorkflowError("Image URI is empty")

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
        image = ":".join(self._get_image_uri_and_tag())

        hostcache = os.path.join(get_appdirs().user_cache_dir, SOURCE_CACHE)
        containercache = os.path.join(SNAKEMAKE_MOUNTPOINT, ".cache", SOURCE_CACHE)

        if not os.path.exists(hostcache):
            hostcache = containercache = tempfile.mkdtemp()

        template = (
            "{service} run"
            " --rm"  # Remove container after execution
            " -e HOME={workdir}"  # Set HOME to working directory
            " -w {workdir}"  # Working directory inside container
            " -v {hostdir}:{workdir}"  # Mount host directory to container
            " -v {hostcache}:{containercache}"  # Mount host cache to container
            " {image_id}"  # Container image
            " {shell}"  # Shell executable
            " -c '{cmd}'"  # The command to execute
        )

        decorated_cmd = template.format(
            service=self.settings.kind,
            workdir=SNAKEMAKE_MOUNTPOINT,
            hostdir=repr(getcwd()),  # TODO: allow to override
            hostcache=repr(hostcache),
            containercache=repr(containercache),
            image_id=image,
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
        uri, tag = self._get_image_uri_and_tag()
        image = SoftwareReport(
            name=uri,
            version=tag,
        )

        # In addition to the image tag, we also want to include the full image id in the version
        # reporting.
        # TODO: can move the managers to the initialization to encapsulate backend-specific logic
        # TODO: we can retrieve the dereferenced URI from the image repo. But different backends
        # have different ways of representing the metadata.
        if self.settings.kind == ContainerType.PODMAN:
            pm = PodmanManager()
        elif self.settings.kind == ContainerType.UDOCKER:
            pm = UDockerManager()
        full_image_id = pm.inspect_image(uri)
        if full_image_id != "":
            image.version = f"{image.version}/{full_image_id}"

        yield image


class UDockerManager:
    cmd = ContainerType.UDOCKER.item_to_choice()

    def inspect_image(self, image_id) -> str:
        try:
            # Run udocker inspect command
            result = subprocess.run(
                [self.cmd, "inspect", image_id],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse the output as JSON
            inspect_data = json.loads(result.stdout)

            # Extract the hash from rootfs.diff_ids
            if "rootfs" in inspect_data and "diff_ids" in inspect_data["rootfs"]:
                if len(inspect_data["rootfs"]["diff_ids"]) > 0:
                    diff_id = inspect_data["rootfs"]["diff_ids"][0]
                    # Remove sha256: prefix if present
                    if diff_id.startswith("sha256:"):
                        return diff_id[7:19]  # First 12 chars after prefix
                    return diff_id[:12]

            return ""  # Return empty string if hash not found

        except (
            subprocess.CalledProcessError,
            json.JSONDecodeError,
            KeyError,
            IndexError,
        ) as e:
            print(f"error: failed to extract hash for udocker image {image_id}: {e}")
            return ""


class PodmanManager:
    cmd = ContainerType.PODMAN.item_to_choice()

    def inspect_image(self, image_id) -> str:
        try:
            result = subprocess.run(
                [self.cmd, "inspect", image_id],
                capture_output=True,
                text=True,
                check=True,
            )
            inspect_data = json.loads(result.stdout)
            full_image_id = inspect_data[0]["Id"]
            truncated = full_image_id[:12]
            return truncated
        except subprocess.CalledProcessError as e:
            print(f"error: failed to inspect image {image_id}: {e}")
            return ""
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"error: failed to parse output for image {image_id}: {e}")
            return ""
