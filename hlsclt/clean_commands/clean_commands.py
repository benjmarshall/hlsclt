# -*- coding: utf-8 -*-
""" Clean up subcommands for HLSCLT.

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click
import shutil
import os

### Supporting Functions###
# Callback function used to exit the program on a negative user prompt response
def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()

# Function to safely handle file deletions and return status
def try_delete(item):
    try:
        shutil.rmtree(item)
    except OSError:
        try:
            os.remove(item)
        except OSError:
            return 1
        else:
            return 0
    else:
        return 0

# Funtion to remove generated files
def clean_up_generated_files(obj):
        config = obj.config
        if try_delete(config["project_name"]) + try_delete("run_hls.tcl") + try_delete("vivado_hls.log") == 3:
            click.echo("Warning: Nothing to remove!")
        else:
            click.echo("Cleaned up generated files.")

### Click Command Definitions ###
# Clean Command
@click.command('clean',short_help='Remove generated files.')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to remove all generated files?',
              help='Force quiet removal.')
@click.pass_obj
def clean(obj):
    """Removes all Vivado HLS generated files and the generated Tcl build script."""
    clean_up_generated_files(obj)
