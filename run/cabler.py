#!/usr/bin/env python

import argparse
import os
import random
import sys
from contextlib import closing
from socket import AF_INET, SOCK_STREAM, socket


class CommandError(Exception):
    pass


class Command:
    """
    We take the content of the 4 config files and roll it into a 
    multidimensioal list which we then use as a template for generating those
    files.
    
    self.topology = {
        "appNodes": ((name, hostname, port), ...),
        "cqcNodes": ((name, hostname, port), ...),
        "Nodes": (name, ...),
        "virtualNodes": ((name, hostname, port), ...),
    }
    """

    def __init__(self):

        config = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', 'config'))

        self.app_nodes = os.path.join(config, 'appNodes.cfg')
        self.cqc_nodes = os.path.join(config, 'cqcNodes.cfg')
        self.nodes = os.path.join(config, 'Nodes.cfg')
        self.vnodes = os.path.join(config, 'virtualNodes.cfg')

        self.topology = {
            "appNodes": [],
            "cqcNodes": [],
            "Nodes": [],
            "virtualNodes": [],
        }
        self.__acquire_current_topology()

        self.parser = argparse.ArgumentParser(
            description='Re-cable the network')

        subparsers = self.parser.add_subparsers(dest='subcommand')

        parser_add = subparsers.add_parser('add', help='Add a node')
        parser_add.add_argument('name', type=str, help='The common name')
        parser_add.add_argument('hostname', type=str, help='The hostname')
        parser_add.add_argument(
            '--app-port',
            type=int,
            help="An available port number for the application node.  If one"
                 "isn't specified, it will be generated)"
        )
        parser_add.add_argument(
            '--cqc-port',
            type=int,
            help="An available port number for the CQC Node.  If one isn't"
                 "specified, it will be generated)"
        )
        parser_add.add_argument(
            '--vnode-port',
            type=int,
            help="An available port number for the virtual node.  If one isn't"
                 "specified, it will be generated)"
        )

        parser_remove = subparsers.add_parser('remove', help='Remove help')
        parser_remove.add_argument(
            'name',
            choices=[_[0] for _ in self.topology['appNodes']]
        )

        self.args = self.parser.parse_args()

    def main(self):

        if not self.args.subcommand:
            self.parser.print_help()
            sys.exit(0)

        try:
            if self.args.subcommand == 'add':

                self.add_node(
                    self.args.name,
                    self.args.hostname,
                    self.args.app_port,
                    self.args.cqc_port,
                    self.args.vnode_port,
                )

            elif self.args.subcommand == 'remove':

                self.remove_node(self.args.name)

            else:

                raise CommandError(
                    "Undefined subcommand.  "
                    "This shouldn't be possible.  "
                    "Stop it."
                )

        except CommandError as e:
            sys.stderr.write("{}\n".format(e))
            sys.exit(1)

        self.__write_all_the_things()

        sys.exit(0)

    def add_node(
            self, 
            name: str, 
            hostname: str, 
            app_port: int = None, 
            cqc_port: int = None, 
            vnode_port: int = None
    ):

        ports = (
            ('appNodes', app_port),
            ('cqcNodes', cqc_port),
            ('virtualNodes', vnode_port)
        )

        for key, port in ports:

            if port:
                if not self.__check_port_available(port):
                    raise CommandError('Port {} is already in use.'.format(
                        port
                    ))
            else:
                port = self.get_random_port()

            self.topology[key].append((name, hostname, port))

        self.topology['Nodes'].append(name)

    def remove_node(self, name):
        for key in ('appNodes', 'cqcNodes', 'Nodes', 'virtualNodes'):
            tmp = []
            for line in self.topology[key]:
                if not line[0] == name:
                    tmp.append(line)
            self.topology[key] = tmp

    def get_random_port(self):
        port = random.randint(8000, 9000)
        if self.__check_port_available(port):
            return port
        return self.get_random_port()

    @staticmethod
    def check_socket_is_free(host: str, port: int) -> bool:
        with closing(socket(AF_INET, SOCK_STREAM)) as sock:
            if sock.connect_ex((host, port)) == 0:
                return False  # Open
            return True  # Closed (available)

    def __check_port_available(self, port):

        for key, config in self.topology.items():

            # No ports defined in this one
            if key == 'Nodes':
                continue

            for line in config:
                _, hostname, *ports = line
                if port in ports:
                    return False
                if not self.check_socket_is_free(hostname, port):
                    return False

        return True

    def __acquire_current_topology(self):
        self.__read_app_nodes()
        self.__read_cqc_nodes()
        self.__read_nodes()
        self.__read_virtual_nodes()

    def __write_all_the_things(self):
        # import json
        # print(json.dumps(self.topology, indent=2))
        self.__write_app_nodes()
        self.__write_cqc_nodes()
        self.__write_nodes()
        self.__write_virtual_nodes()

    # A lot of the following is copypasta, but I'm leaving it this way with the
    # assumption that there's something about these files that I'm not yet
    # aware of.

    def __read_app_nodes(self):
        with open(self.app_nodes, 'r') as r:
            for line in r:
                if line.startswith('#'):
                    continue
                if not line.strip():
                    continue
                name, hostname, port = [_.strip() for _ in line.split(',')]
                self.topology['appNodes'].append((name, hostname, int(port)))

    def __read_cqc_nodes(self):
        with open(self.cqc_nodes, 'r') as r:
            for line in r:
                if line.startswith('#'):
                    continue
                if not line.strip():
                    continue
                name, hostname, port = [_.strip() for _ in line.split(',')]
                self.topology['cqcNodes'].append((name, hostname, int(port)))

    def __read_nodes(self):
        with open(self.nodes, 'r') as r:
            for line in r:
                line = line.strip()
                if line.startswith('#'):
                    continue
                if not line:
                    continue
                self.topology['Nodes'].append(line)

    def __read_virtual_nodes(self):
        with open(self.vnodes, 'r') as r:
            for line in r:
                if line.startswith('#'):
                    continue
                if not line.strip():
                    continue
                name, hostname, port = [_.strip() for _ in line.split(',')]
                self.topology['virtualNodes'].append(
                    (name, hostname, int(port))
                )

    def __write_app_nodes(self):
        with open(self.app_nodes, 'w') as f:
            for line in self.topology['appNodes']:
                f.write('{}, {}, {}\n'.format(*line))

    def __write_cqc_nodes(self):
        with open(self.cqc_nodes, 'w') as f:
            for line in self.topology['cqcNodes']:
                f.write('{}, {}, {}\n'.format(*line))

    def __write_nodes(self):
        with open(self.nodes, 'w') as f:
            for line in self.topology['Nodes']:
                f.write(line + "\n")

    def __write_virtual_nodes(self):
        with open(self.vnodes, 'w') as f:
            for line in self.topology['virtualNodes']:
                f.write('{}, {}, {}\n'.format(*line))


if __name__ == '__main__':
    Command().main()