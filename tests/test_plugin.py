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

# There can be multiple subclasses of SoftwareDeploymentProviderBase here.
# This way, you can implement multiple test scenarios.
# For each subclass, the test suite tests the environment activation and execution
# within, and, if applicable, environment deployment and archiving.


class TestUDockerContainer(TestSoftwareDeploymentBase):
    __test__ = True  # activate automatic testing

    test_container = "alpine:latest"
    runtime = Runtime.UDOCKER

    def get_env_spec(self) -> EnvSpecBase:
        # If the software deployment provider does not support deployable environments,
        # this method should return an existing environment spec that can be used
        # for testing
        return EnvSpec(self.test_container)

    def get_env_cls(self) -> Type[EnvBase]:
        # Return the environment class that should be tested.
        return Env

    def get_software_deployment_provider_settings(
        self,
    ) -> Optional[SoftwareDeploymentSettingsBase]:
        return Settings(runtime=self.runtime)

    def get_test_cmd(self) -> str:
        # Return a test command that should be executed within the environment
        # with exit code 0 (i.e. without error).
        return "/bin/true"


# Helper function to check if podman is available
def is_podman_available():
    return shutil.which("podman") is not None


@pytest.mark.skipif(
    not is_podman_available(), reason="podman not available on the system"
)
class TestPodmanContainer(TestSoftwareDeploymentBase):
    __test__ = True  # activate automatic testing

    test_container = "alpine:latest"
    runtime = Runtime.PODMAN

    def get_env_spec(self) -> EnvSpecBase:
        # If the software deployment provider does not support deployable environments,
        # this method should return an existing environment spec that can be used
        # for testing
        return EnvSpec(self.test_container)

    def get_env_cls(self) -> Type[EnvBase]:
        # Return the environment class that should be tested.
        return Env

    def get_software_deployment_provider_settings(
        self,
    ) -> Optional[SoftwareDeploymentSettingsBase]:
        return Settings(runtime=self.runtime)

    def get_test_cmd(self) -> str:
        # Return a test command that should be executed within the environment
        # with exit code 0 (i.e. without error).
        return "/bin/true"
