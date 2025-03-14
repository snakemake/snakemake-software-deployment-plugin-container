import subprocess as sp
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
    ContainerSettings,
    ContainerSpec,
    ContainerEnv,
    ContainerType,
)

# There can be multiple subclasses of SoftwareDeploymentProviderBase here.
# This way, you can implement multiple test scenarios.
# For each subclass, the test suite tests the environment activation and execution
# within, and, if applicable, environment deployment and archiving.


class TestUDockerContainer(TestSoftwareDeploymentBase):
    __test__ = True  # activate automatic testing

    test_container = "alpine:latest"
    kind = ContainerType.UDOCKER

    def get_env_spec(self) -> EnvSpecBase:
        # If the software deployment provider does not support deployable environments,
        # this method should return an existing environment spec that can be used
        # for testing
        return ContainerSpec(self.test_container)

    def get_env_cls(self) -> Type[EnvBase]:
        # Return the environment class that should be tested.
        return ContainerEnv

    def get_software_deployment_provider_settings(
        self,
    ) -> Optional[SoftwareDeploymentSettingsBase]:
        return ContainerSettings(kind=self.kind)

    def get_test_cmd(self) -> str:
        # Return a test command that should be executed within the environment
        # with exit code 0 (i.e. without error).
        return "/bin/true"

    def test_report_software(self, tmp_path):
        env = self._get_env(tmp_path)
        cmd = self.get_test_cmd()
        decorated_cmd = env.managed_decorate_shellcmd(cmd)

        # force the run to actually fetch the image
        # TODO: there might be a better way to test this after the automatic
        # testing has actually been called
        sp.run(decorated_cmd, shell=True, executable=self.shell_executable)
        rep = tuple(env.report_software())

        # check the first software reported, should be the container
        # We're reporting version as the tag + the hash of the image
        # latest/aded1e1a5b37
        assert rep[0].name == "alpine"
        assert len(rep[0].version) == 19
        assert rep[0].version.startswith("latest/")


# Helper function to check if podman is available
def is_podman_available():
    return shutil.which("podman") is not None


@pytest.mark.skipif(
    not is_podman_available(), reason="podman not available on the system"
)
class TestPodmanContainer(TestSoftwareDeploymentBase):
    __test__ = True  # activate automatic testing

    test_container = "alpine:latest"
    kind = ContainerType.PODMAN

    def get_env_spec(self) -> EnvSpecBase:
        # If the software deployment provider does not support deployable environments,
        # this method should return an existing environment spec that can be used
        # for testing
        return ContainerSpec(self.test_container)

    def get_env_cls(self) -> Type[EnvBase]:
        # Return the environment class that should be tested.
        return ContainerEnv

    def get_software_deployment_provider_settings(
        self,
    ) -> Optional[SoftwareDeploymentSettingsBase]:
        return ContainerSettings(kind=self.kind)

    def get_test_cmd(self) -> str:
        # Return a test command that should be executed within the environment
        # with exit code 0 (i.e. without error).
        return "/bin/true"

    # This test is optional; we are interested in peeking beyond the interface
    # and make sure we're getting specific information from the container.
    def test_report_software(self, tmp_path):
        env = self._get_env(tmp_path)
        cmd = self.get_test_cmd()
        decorated_cmd = env.managed_decorate_shellcmd(cmd)

        # force the run to actually fetch the image
        sp.run(decorated_cmd, shell=True, executable=self.shell_executable)
        rep = tuple(env.report_software())

        # check the first software reported, should be the container
        # We're reporting version as the tag + the hash of the image
        # latest/aded1e1a5b37
        assert rep[0].name == "alpine"
        assert len(rep[0].version) == 19
        assert rep[0].version.startswith("latest/")
