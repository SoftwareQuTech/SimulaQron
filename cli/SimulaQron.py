#!/usr/bin/env python3
import click

from simulaqron.commands.network import network

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """Command line interface for interacting with SimulaQron."""
    pass


cli.add_command(network)

if __name__ == "__main__":
    cli()
