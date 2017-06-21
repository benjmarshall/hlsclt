# -*- coding: utf-8 -*-
""" A Vivado HLS Command Line Helper tool

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click
from ._version import __version__
import os
from .classes import *
from .helper_funcs import *
from .clean_commands import clean_commands
from .build_commands import build_commands
from .report_commands import report_commands

### Main Click Entry Point ###
@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """Helper tool for using Vivado HLS through the command line. If no arguments are specified then a default run is executed which includes C simulation, C synthesis, Cosimulation and export for both Vivado IP Catalog and System Generator. If any of the run options are specified then only those specified are performed."""
    # Generate a default config dict and then load in the local config file.
    config = generate_default_config();
    config_loaded = get_vars_from_file('hls_config.py')
    errors = []
    parse_config_vars(config_loaded, config, errors)
    if len(errors) != 0:
        for err in errors:
            print(err)
        print("Config Errors, exiting...")
        raise click.Abort()
    # Store the loaded config in an object within the Click context so it is available to all commands.
    obj = hlsclt_internal_object(config)
    ctx.obj = obj
    pass

# Add Click Sub Commands
cli.add_command(clean_commands.clean)
cli.add_command(build_commands.build)
cli.add_command(report_commands.report)
cli.add_command(report_commands.open_gui)
cli.add_command(report_commands.status)
