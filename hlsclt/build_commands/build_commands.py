# -*- coding: utf-8 -*-
""" Build related subcommands for HLSCLT.

Copyright (c) 2017 Ben Marshall
"""

import click
import subprocess
import os
from hlsclt.report_commands.report_commands import open_report
from hlsclt.helper_funcs import (create_solution, complete_solution,
                                 set_active_solution)
from hlsclt.classes import ConfigError
from hlsclt.tcl_commands import\
    (open_project, open_solution, set_top, add_files, set_part, create_clock,
     cosim_design, exit, export_design, csim_design, csynth_design, source,
     set_directive)


# Supporting Functions
# Function to generate the 'pre-amble' within the HLS Tcl build script.
def do_start_build_stuff(config, script):
    script.append(open_project(config.project_name))
    script.append(set_top(config.active_solution.top_level_function_name))
    script.extend(add_files(config.src_files,
                            cflags=config.cflags))
    script.extend(add_files(config.tb_files,
                            cflags=config.tb_cflags, is_tb=True))
    script.extend(add_files(config.active_solution.src_files,
                            cflags=config.cflags))
    script.extend(add_files(config.active_solution.tb_files,
                            cflags=config.tb_cflags, is_tb=True))
    script.append(open_solution(config.solution))
    script.append(set_part(config.part_name))
    script.append(create_clock(config.clock_period))
    script.extend(map(set_directive, config.active_solution.directives))
    script.extend(map(source, config.active_solution.source))


# Function to write a default build into the HLS Tcl build script.
def do_default_build(config, script):
    script.append(csim_design(config.compiler))
    script.append(csynth_design())
    script.append(cosim_design(config.language))
    script.append(export_design(format="ip_catalog"))
    script.append(export_design(format="sysgen"))


# Function which defines the main actions of the 'csim' command.
def do_csim_stuff(config, script):
    script.append(csim_design(config.compiler))


# Function which defines the main actions of the 'syn' command.
def do_syn_stuff(config, script):
    script.append(csynth_design())


# Function which defines the main actions of the 'cosim' command.
def do_cosim_stuff(config, script, debug):
    trace_level = "all" if debug else ""
    script.append(cosim_design(config.language, trace_level))


# Function which defines the main actions of the 'export' command.
def do_export_stuff(config, script, type, evaluate):
    evaluate = config.language if evaluate else ""
    if "ip" in type:
        script.append(export_design(format="ip_catalog", evaluate=evaluate))
    if "sysgen" in type:
        script.append(export_design(format="sysgen", evaluate=evaluate))


# Function to perform a search for existing c synthesis results
# in a specified hls project and solution.
def check_for_syn_results(proj_name, solution, top_level_function_name):
    return os.path.isfile("%s/%s/syn/report/%s_csynth.rpt"
                          % (proj_name, solution, top_level_function_name))


# Function to check is C synthesis is going to be required
# but may have been forgorgotten by the user.
def syn_lookahead_check(config, script, syn_command_present):
    syn_result = check_for_syn_results(config.project_name,
                                       config.solution,
                                       config.top_level_function_name)
    if not (syn_command_present or syn_result):
        if click.confirm("C Synthesis has not yet been run, "
                         + "but is required for the process(es)"
                         + "you have selected.\nWould you like to add"
                         + "it to this run?", default=True):
            click.echo("Adding csynth option.")
            script.append(csynth_design(config.compiler))
        else:
            click.echo("Ok, watch out for missing synthesis errors!")


# Function which defines the actions that occur after a HLS build.
def do_end_build_stuff(config, script, sub_command_returns, report):
    # Copy the src/ files as well as the config file
    # to keep track of the changes over solutions
    # click.echo("Copying the source and config files to solution: %s" %
    #            config.solution)
    # destiny = os.path.join(config.project_name, config.solution)
    # destiny_src = os.path.join(destiny, "src")

    # # If we are overwriting an existing solution delete the source directory
    # shutil.rmtree(destiny_src, ignore_errors=True)
    # shutil.copytree("src", destiny_src)

    # Check for reporting flag
    if report:
        if not sub_command_returns:
            # Must be on the default run, add all stages manually
            sub_command_returns = ['csim', 'syn', 'cosim', 'export']
        for report in sub_command_returns:
            open_report(config, report)


# Click Command Definitions

# Build group entry point
@click.group(chain=True, invoke_without_command=True,
             short_help='Run HLS build stages.')
@click.option('-r', '--report', is_flag=True,
              help='Open build reports when finished.')
@click.option('-s', '--solution', type=click.Path(),
              shell_complete=complete_solution,
              help='Use the specified solution', required=False)
@click.pass_context
def build(ctx, report, solution):
    """Runs the Vivado HLS tool and executes the specified build stages."""
    if solution:
        try:
            set_active_solution(ctx.obj.config, solution)
        except ConfigError as e:
            click.echo(e, err=True)
    create_solution(ctx.obj.config.project_name, ctx.obj.config.solution)
    do_start_build_stuff(ctx.obj.config, ctx.obj.script)


# Callback which executes when all specified build subcommands finished.
@build.resultcallback()
@click.pass_context
def build_end_callback(ctx, sub_command_returns, report, solution):
    # Catch the case where no subcommands have been issued and offer a default
    if not sub_command_returns:
        if click.confirm("No build stages specified,"
                         + "would you like to run a default sequence"
                         + "using all the build stages?", abort=True):
            do_default_build(ctx.obj.config, ctx.obj.script)

    # Write the script to file
    config = ctx.obj.config
    script = ctx.obj.script
    script.append(exit())
    try:
        path = os.path.join(config.project_name, config.solution, "script.tcl")
        with click.open_file(path, "w") as file:
            file.write("\n".join(script))
    except (OSError, IOError):
        click.echo("Couldn't create a Tcl run file in the solution folder!")
        raise click.Abort()

    # Call the Vivado HLS process
    returncode = subprocess.call(["vivado_hls", "-f", path])

    # Check return status of the HLS process.
    if returncode < 0:
        raise click.Abort()
    elif returncode > 0 and report:
        click.echo("Warning: HLS Process returned an error,"
                   + "skipping report opening!")
        raise click.Abort()
    else:
        do_end_build_stuff(ctx.obj.config, ctx.obj.script,
                           sub_command_returns, report)


# csim subcommand
@build.command('csim')
@click.pass_context
def csim(ctx):
    """Runs the Vivado HLS C simulation stage."""
    config = ctx.obj.config
    do_csim_stuff(config, ctx.obj.script)
    return 'csim'


# syn subcommand
@build.command('syn')
@click.pass_context
def syn(ctx):
    """Runs the Vivado HLS C synthesis stage."""
    do_syn_stuff(ctx.obj.config, ctx.obj.script)
    ctx.obj.syn_command_present = True
    return 'syn'


# cosim subcommand
@build.command('cosim')
@click.option('-d', '--debug', is_flag=True,
              help="Turns off compile optimisations"
                   + " and enables logging for cosim.")
@click.pass_context
def cosim(ctx, debug):
    """Runs the Vivado HLS cosimulation stage."""
    syn_lookahead_check(ctx.obj.config, ctx.obj.script,
                        ctx.obj.syn_command_present)
    do_cosim_stuff(ctx.obj.config, ctx.obj.script, debug)
    return 'cosim'


# export subcommand
@build.command('export')
@click.option('-t', '--type',  required=True, multiple=True,
              type=click.Choice(['ip', 'sysgen']),
              help="Specify an export type, Vivado IP Catalog or "
                   + "System Generator. Accepts multiple occurences.")
@click.option('-e', '--evaluate', is_flag=True,
              help="Runs Vivado synthesis and place "
                   + "and route for the generated export.")
@click.pass_context
def export(ctx, type, evaluate):
    """Runs the Vivado HLS export stage."""
    syn_lookahead_check(ctx.obj.config, ctx.obj.script,
                        ctx.obj.syn_command_present)
    do_export_stuff(ctx.obj.config, ctx.obj.script, type, evaluate)
    return 'export'
