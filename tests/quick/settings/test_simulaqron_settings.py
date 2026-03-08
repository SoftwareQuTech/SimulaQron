import json
import pytest
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from dataclasses_serialization.json import JSONSerializer

from simulaqron.settings import simulaqron_settings
from simulaqron.settings.simulaqron_config import (SimulaqronConfig,
                                                   DEFAULT_SIMULAQRON_SETTINGS_FILENAME)


cwd_settings = (Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME).resolve()
home_settings = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_SETTINGS_FILENAME).resolve()


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
        if home_settings.exists() and home_settings.is_file():
            orig_home_settings = NamedTemporaryFile(suffix=".json", mode="w", delete_on_close=False).__enter__()
            shutil.copyfile(home_settings, orig_home_settings.name)
            home_settings.unlink()
        else:
            orig_home_settings = None
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

    @staticmethod
    def _cleanup_config_files():
        files_to_check = [cwd_settings, home_settings]
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
            "sim_backend": "qutip",
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

        TestSettings._cleanup_config_files()

    def test_load_non_existent_config_file(self):
        with pytest.raises(FileNotFoundError) as error:
            simulaqron_settings.read_from_file("/non/existent/file")
        assert "No such file or directory: '/non/existent/file'" in str(error.value)
