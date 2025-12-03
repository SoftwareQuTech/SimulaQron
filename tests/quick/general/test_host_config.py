from pathlib import Path

import pytest

from simulaqron.general.host_config import SocketsConfig
from simulaqron.settings import network_config
from simulaqron.settings.network_config import NodeConfigType


class TestSocketsConfig:
    @staticmethod
    def _assert_results(app_conf: SocketsConfig, qnodeos_conf: SocketsConfig, vnode_conf: SocketsConfig):
        assert len(app_conf.hostDict) == 2
        assert "Alice" in app_conf.hostDict
        assert "Bob" in app_conf.hostDict
        assert app_conf.hostDict["Alice"].port == 8000
        assert app_conf.hostDict["Bob"].port == 8003

        assert len(qnodeos_conf.hostDict) == 2
        assert "Alice" in qnodeos_conf.hostDict
        assert "Bob" in qnodeos_conf.hostDict
        assert qnodeos_conf.hostDict["Alice"].port == 8001
        assert qnodeos_conf.hostDict["Bob"].port == 8004

        assert len(vnode_conf.hostDict) == 2
        assert "Alice" in vnode_conf.hostDict
        assert "Bob" in vnode_conf.hostDict
        assert vnode_conf.hostDict["Alice"].port == 8002
        assert vnode_conf.hostDict["Bob"].port == 8005

    @pytest.mark.skip(reason="Reading network config from legacy format files is not implemented yet")
    def test_load_legacy_net_config_file(self):
        this_file_folder = Path(__file__).parent
        sockets_config_path = this_file_folder / "resources" / "sockets.cfg"
        qnodeos_config_path = this_file_folder / "resources" / "qnodeos.cfg"
        virtual_config_path = this_file_folder / "resources" / "virtual.cfg"
        network_config.read_from_legacy_files(app_file_path=sockets_config_path,
                                              qnodeos_config_path=qnodeos_config_path,
                                              virtual_config_path=virtual_config_path)

        app_conf = SocketsConfig(network_config, config_type=NodeConfigType.APP)
        qnodeos_conf = SocketsConfig(network_config, config_type="qnodeos")
        vnode_conf = SocketsConfig(network_config)

        TestSocketsConfig._assert_results(app_conf, qnodeos_conf, vnode_conf)

    def test_load_new_net_config_file(self):
        this_file_folder = Path(__file__).parent
        network_config_path = this_file_folder / "resources" / "network.json"
        network_config.read_from_file(network_config_path)

        app_conf = SocketsConfig(network_config, config_type=NodeConfigType.APP)
        qnodeos_conf = SocketsConfig(network_config, config_type="qnodeos")
        vnode_conf = SocketsConfig(network_config)

        TestSocketsConfig._assert_results(app_conf, qnodeos_conf, vnode_conf)
