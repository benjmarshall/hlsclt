# -*- coding: utf-8 -*-
""" A Vivado HLS Command Line Helper tool

Copyright (c) 2017 Ben Marshall
"""

import click
from ._version import __version__
from .classes import hlsclt_internal_object, ConfigError
from .helper_funcs import load_config
from .clean_commands import clean_commands
from .build_commands import build_commands
from .report_commands import report_commands


# Main Click Entry Point
@click.group()
@click.version_option(version=__version__)
@click.option('-c', '--config-file', 'config_file',
              default="hls_config.yaml", type=click.File('r'))
@click.option('-d', '--debug', 'debug', default=False, is_flag=True)
@click.pass_context
def cli(ctx, config_file, debug):
    """\
Helper tool for using Vivado HLS through the command line.
If no arguments are specified then a default run is executed which
includes C simulation, C synthesis, Cosimulation and export for both
Vivado IP Catalog and System Generator. If any of the run options are
specified then only those specified are performed.
    """
    try:
        config = load_config(config_file)
        ctx.obj = hlsclt_internal_object(config, debug)
    except ConfigError as e:
        for err in e.errors:
            click.echo(err, err=True)
        click.echo("Config Errors", err=True)
        raise click.Abort()
    except Exception as e:
        if debug:
            from traceback import format_exc
            click.echo(format_exc(), err=True)
        else:
            click.echo(e, err=True)
        click.echo("Unexpected Errors %s"
                   % ("" if debug else "(pass -d/--debug for traceback)"),
                   err=True)
        raise click.Abort()
    pass


# Add Click Sub Commands
cli.add_command(clean_commands.clean)
cli.add_command(build_commands.build)
cli.add_command(report_commands.report)
cli.add_command(report_commands.open_gui)
cli.add_command(report_commands.status)
