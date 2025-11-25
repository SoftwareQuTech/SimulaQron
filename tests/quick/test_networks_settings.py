import json
import pytest
import shutil
from importlib import resources
from pathlib import Path
from tempfile import NamedTemporaryFile
from dataclasses_serialization.json import JSONSerializer

import simulaqron._default_config
from simulaqron.settings import network_config, NetworkConfigBuilder
from simulaqron.settings.network_config import DEFAULT_SIMULAQRON_NETWORK_FILENAME


cwd_network = (Path.cwd() / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()
home_network = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()

class TestNetworksSettings:
    @pytest.fixture
    def clean_settings(self):
        # Load the setting files in cwd and home, saved them in a temp file
        if cwd_network.is_file() and cwd_network.is_file():
            orig_cwd_network = NamedTemporaryFile(suffix=".json", mode="w", delete_on_close=False).__enter__()
            shutil.copyfile(cwd_network, orig_cwd_network.name)
            cwd_network.unlink()
        else:
            orig_cwd_network = None
        if home_network.is_file() and home_network.is_file():
            orig_home_network = NamedTemporaryFile(suffix=".json", mode="w", delete_on_close=False).__enter__()
            shutil.copyfile(home_network, orig_home_network.name)
            home_network.unlink()
        else:
            orig_home_network = None
        # Proceed with the test case
        yield
        # Restore the loaded files in the original locations
        if orig_cwd_network is not None:
            cwd_network.touch()
            shutil.copyfile(orig_cwd_network.name, cwd_network)
            orig_cwd_network.__exit__(None, None, None)
        if orig_home_network is not None:
            home_network.touch()
            shutil.copyfile(orig_home_network.name, home_network)
            orig_home_network.__exit__(None, None, None)

        files_to_check = [cwd_network, home_network]
        for file in files_to_check:
            if file.exists() and file.is_file():
                file.unlink()

    def test_create_default_settings(self, clean_settings):
        # Load the "raw" default network
        default_network_path = Path(str(resources.files(simulaqron._default_config).joinpath("default_network.json")))

        expected_net_cfg_dict = json.loads(default_network_path.read_text())
        expected_net_cfg = JSONSerializer.deserialize(NetworkConfigBuilder, expected_net_cfg_dict)

        assert network_config == expected_net_cfg
