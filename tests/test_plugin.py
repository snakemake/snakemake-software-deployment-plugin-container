from typing import Optional, Type

import pytest
import shutil

from snakemake_interface_software_deployment_plugins.tests import (
    TestSoftwareDeploymentBase,
)
from snakemake_interface_software_deployment_plugins import (
    EnvSpecBase,
    EnvBase,
)
from snakemake_interface_software_deployment_plugins.settings import (
    SoftwareDeploymentSettingsBase,
)

from snakemake_software_deployment_plugin_container import (
    Settings,
    EnvSpec,
    Env,
    Runtime,
)


class TestBase(TestSoftwareDeploymentBase):
    test_container = "quay.io/biocontainers/samtools:1.23.1--ha83d96e_0"

    def get_contained_executable(self) -> str:
        # just provide something that is available inside of the container
        return "samtools"

    def get_env_spec(self) -> EnvSpecBase:
        # If the software deployment provider does not support deployable environments,
        # this method should return an existing environment spec that can be used
        # for testing
        return EnvSpec(self.test_container)

    def get_env_cls(self) -> Type[EnvBase]:
        # Return the environment class that should be tested.
        return Env

    def get_settings_cls(self) -> Optional[Type[SoftwareDeploymentSettingsBase]]:
        return Settings

    def get_test_cmd(self) -> str:
        # Return a test command that should be executed within the environment
        # with exit code 0 (i.e. without error).
        return "samtools --version"


class TestApptainerContainer(TestBase):
    __test__ = True

    def get_settings(
        self,
    ) -> Optional[SoftwareDeploymentSettingsBase]:
        return Settings(runtime=Runtime.APPTAINER)


class TestUDockerContainer(TestBase):
    __test__ = True  # activate automatic testing

    def get_settings(
        self,
    ) -> Optional[SoftwareDeploymentSettingsBase]:
        return Settings(runtime=Runtime.UDOCKER)


def is_podman_available():
    return shutil.which("podman") is not None


def is_docker_available():
    return shutil.which("docker") is not None


@pytest.mark.skipif(
    not is_podman_available(), reason="podman not available on the system"
)
class TestPodmanContainer(TestBase):
    __test__ = True  # activate automatic testing

    def get_settings(
        self,
    ) -> Optional[SoftwareDeploymentSettingsBase]:
        return Settings(runtime=Runtime.PODMAN)


@pytest.mark.skipif(
    not is_docker_available(), reason="docker not available on the system"
)
class TestDockerContainer(TestBase):
    __test__ = True  # activate automatic testing

    def get_settings(
        self,
    ) -> Optional[SoftwareDeploymentSettingsBase]:
        return Settings(runtime=Runtime.DOCKER)
