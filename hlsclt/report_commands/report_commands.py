# -*- coding: utf-8 -*-
""" Report subcommands for HLSCLT.

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click

### Click Command Definitions ###
# Report Command
@click.command('report',short_help='Open reports.')
def report():
    """Opens the Vivado HLS report for the chosen build stages."""
    click.echo("Report Mode")
