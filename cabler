#!/usr/bin/env python

import argparse
import os
import random
import sys


class CommandError(Exception):
    pass


class Command:

    def __init__(self):

        self.config = os.path.join(os.path.dirname(__file__), 'config')

        self.topology = []
        self.__acquire_current_topology()

        self.parser = argparse.ArgumentParser(
            description='Re-cable the network')

        subparsers = self.parser.add_subparsers(dest='subcommand')

        parser_add = subparsers.add_parser('add', help='Add a node')
        parser_add.add_argument('name', type=str, help='The common name')
        parser_add.add_argument('hostname', type=str, help='The hostname')
        parser_add.add_argument(
            'port',
            type=int,
            nargs='?',
            help="An available port number (if one isn't specified, it will "
                 "be generated)"
        )

        parser_remove = subparsers.add_parser('remove', help='Remove help')
        parser_remove.add_argument(
            'name',
            choices=[_[0] for _ in self.topology]
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
                    self.args.port
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

    def add_node(self, name, hostname, port):

        if port in [_[2] for _ in self.topology]:
            raise CommandError("That port is already in use.")

        if not port:
            port = self.__get_random_port()

        sys.stdout.write("Adding {} to the network at {}:{}\n".format(
            name, hostname, port))

        self.topology.append((
            name,
            hostname,
            port
        ))

    def remove_node(self, name):

        sys.stdout.write("Removing {} from the network\n".format(name))

        tmp = []
        for line in self.topology:
            if not line[0] == name:
                tmp.append(line)
        self.topology = tmp

    def __get_random_port(self):
        port = random.randint(8000, 9000)
        if port not in [_[2] for _ in self.topology]:
            return port
        return self.__get_random_port()

    def __write_all_the_things(self):
        self.__update_app_nodes()
        self.__update_classic_net()
        self.__update_cqc_nodes()
        self.__update_nodes()
        self.__update_virtual_nodes()

    def __acquire_current_topology(self):
        with open(os.path.join(self.config, 'appNodes.cfg'), 'r') as r:
            for line in r:
                if line.startswith('#'):
                    continue
                if not line.strip():
                    continue
                name, hostname, port = [_.strip() for _ in line.split(',')]
                self.topology.append((name, hostname, int(port)))

    # A lot of the following is copypasta, but I'm leaving it this way with the
    # assumption that there's something about these files that I'm not yet
    # aware of.

    def __update_app_nodes(self):
        with open(os.path.join(self.config, 'appNodes.cfg'), 'w') as f:
            for line in self.topology:
                f.write('{}, {}, {}\n'.format(*line))

    def __update_classic_net(self):
        with open(os.path.join(self.config, 'classicalNet.cfg'), 'w') as f:
            for line in self.topology:
                f.write('{}, {}, {}\n'.format(*line))

    def __update_cqc_nodes(self):
        with open(os.path.join(self.config, 'cqcNodes.cfg'), 'w') as f:
            for line in self.topology:
                f.write('{}, {}, {}\n'.format(*line))

    def __update_nodes(self):
        with open(os.path.join(self.config, 'Nodes.cfg'), 'w') as f:
            for line in self.topology:
                f.write(line[0])

    def __update_virtual_nodes(self):
        with open(os.path.join(self.config, 'virtualNodes.cfg'), 'w') as f:
            for line in self.topology:
                f.write('{}, {}, {}\n'.format(*line))


if __name__ == '__main__':
    Command().main()
