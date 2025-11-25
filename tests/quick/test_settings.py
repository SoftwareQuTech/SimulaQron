import json
import pytest
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from dataclasses_serialization.json import JSONSerializer

from simulaqron.settings import simulaqron_settings
from simulaqron.settings.simulaqron_config import (SimulaqronConfig,
                                                   DEFAULT_SIMULAQRON_NETWORK_FILENAME,
                                                   DEFAULT_SIMULAQRON_SETTINGS_FILENAME)


cwd_settings = (Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME).resolve()
cwd_network = (Path.cwd() / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()
home_settings = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_SETTINGS_FILENAME).resolve()
home_network = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()


class TestSettings:
    @pytest.fixture
    def clean_settings(self):
        # Load the setting files in cwd and home, saved them in a temp file
        if cwd_settings.exists() and cwd_settings.is_file():
            orig_cwd_settings = NamedTemporaryFile(suffix=".json", mode="w", delete_on_close=False).__enter__()
            shutil.copyfile(cwd_settings, orig_cwd_settings.name)
            cwd_settings.unlink()
        else:
            orig_cwd_settings = None
        if cwd_network.is_file() and cwd_network.is_file():
            orig_cwd_network = NamedTemporaryFile(suffix=".json", mode="w", delete_on_close=False).__enter__()
            shutil.copyfile(cwd_network, orig_cwd_network.name)
            cwd_network.unlink()
        else:
            orig_cwd_network = None
        if home_settings.exists() and home_settings.is_file():
            orig_home_settings = NamedTemporaryFile(suffix=".json", mode="w", delete_on_close=False).__enter__()
            shutil.copyfile(home_settings, orig_home_settings.name)
            home_settings.unlink()
        else:
            orig_home_settings = None
        if home_network.is_file() and home_network.is_file():
            orig_home_network = NamedTemporaryFile(suffix=".json", mode="w", delete_on_close=False).__enter__()
            shutil.copyfile(home_network, orig_home_network.name)
            home_network.unlink()
        else:
            orig_home_network = None
        # Proceed with the test case
        yield
        # Restore the loaded files in the original locations
        if orig_cwd_settings is not None:
            cwd_settings.touch()
            shutil.copyfile(orig_cwd_settings.name, cwd_settings)
            orig_cwd_settings.__exit__(None, None, None)
        if orig_home_settings is not None:
            home_settings.touch()
            shutil.copyfile(orig_home_settings.name, home_settings)
            orig_home_settings.__exit__(None, None, None)
        if orig_cwd_network is not None:
            cwd_network.touch()
            shutil.copyfile(orig_cwd_network.name, cwd_network)
            orig_cwd_network.__exit__(None, None, None)
        if orig_home_network is not None:
            home_network.touch()
            shutil.copyfile(orig_home_network.name, home_network)
            orig_home_network.__exit__(None, None, None)

    @staticmethod
    def _cleanup_config_files():
        files_to_check = [cwd_settings, cwd_network, home_settings, home_network]
        for file in files_to_check:
            if file.exists() and file.is_file():
                file.unlink()

    def test_create_default_settings(self, clean_settings):
        __expected_default_settings = """
        {
            "max_qubits": 20,
            "max_registers": 1000,
            "conn_retry_time": 0.5,
            "conn_max_retries": 10,
            "recv_timeout": 100,
            "recv_retry_time": 0.1,
            "recv_max_retries": 10,
            "log_level": 30,
            "sim_backend": "stabilizer",
            "network_config_file": "HOME_SETTINGS_PATH",
            "noisy_qubits": false,
            "t1": 1.0
        }
        """
        simulaqron_settings.default_settings()
        expected_settings_dict = json.loads(__expected_default_settings)
        path = (Path.home() / ".simulaqron" / "simulaqron_network.json").resolve()
        expected_settings_dict["network_config_file"] = str(path)
        expected_settings = JSONSerializer.deserialize(SimulaqronConfig, expected_settings_dict)

        assert simulaqron_settings == expected_settings

        assert simulaqron_settings.network_builder is not None
        assert simulaqron_settings.network_config_file.exists()
        assert simulaqron_settings.network_config_file.is_file()

        TestSettings._cleanup_config_files()

    def test_non_existent_network_config(self):
        _original_settings = """
        {
            "_read_user": false,
            "max_qubits": 10,
            "max_registers": 500,
            "conn_retry_time": 0.25,
            "recv_timeout": 10,
            "recv_retry_time": 0.05,
            "log_level": 30,
            "sim_backend": "projectq",
            "network_config_file": "/not/existing/network.json",
            "noisy_qubits": false,
            "t1": 2.0
        }
        """
        _expected_settings = """
        {
            "_read_user": false,
            "max_qubits": 10,
            "max_registers": 500,
            "conn_retry_time": 0.25,
            "recv_timeout": 10,
            "recv_retry_time": 0.05,
            "log_level": 30,
            "sim_backend": "projectq",
            "network_config_file": "/not/existing/network.json",
            "noisy_qubits": false,
            "t1": 2.0
        }
        """
        expected_settings_dict = json.loads(_expected_settings)
        expected_settings = JSONSerializer.deserialize(SimulaqronConfig, expected_settings_dict)

        _original_settings = json.loads(_original_settings)
        with NamedTemporaryFile(mode="w+", encoding="utf-8", delete_on_close=False) as file:
            json.dump(_original_settings, file)
            file.close()

            simulaqron_settings.load_from_file(Path(file.name))
            assert simulaqron_settings == expected_settings

    def test_load_non_existent_config_file(self):
        with pytest.raises(FileNotFoundError) as error:
            simulaqron_settings.load_from_file("/non/existent/file")
        assert "No such file or directory: '/non/existent/file'" in str(error.value)
