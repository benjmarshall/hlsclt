# -*- coding: utf-8 -*-
""" Report subcommands for HLSCLT.

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click
import os
from hlsclt.helper_funcs import just_loop_on

### Supporting Functions ###
# Function for opening reports.
def open_report(ctx,report):
    config = ctx.obj.config
    solution_num = ctx.obj.solution_num
    report_files = []
    if report == 'csim':
        report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/csim/report/" + config["top_level_function_name"] + "_csim.log")
    elif report == 'syn':
        report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/syn/report/" + config["top_level_function_name"] + "_csynth.rpt")
    elif report == 'cosim':
        report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/sim/report/" + config["top_level_function_name"] + "_cosim.rpt")
        for language in just_loop_on(config["language"]):
            report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/sim/report/" + config["language"] + "/" + config["top_level_function_name"] + ".log")
    elif report == 'export':
        for language in just_loop_on(config["language"]):
            report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/sim/report/" + config["language"] + "/" + config["top_level_function_name"] + "_export.rpt")
    for file in report_files:
        return_val = os.system('xdg-open ' + file + ' >/dev/null 2>&1')
        if return_val != 0:
            click.echo("Error: Looks like the " + report + " report doesn't exist for project: " + config["project_name"] + ", solution number: " + str(solution_num) + ". Make sure you have run that build stage.")


### Click Command Definitions ###
# Report Command
@click.command('report', short_help='Open reports.')
@click.option('-s', '--stage', required=True, multiple=True,
                type=click.Choice(['csim','syn','cosim','export']),
                help='Which build stage to open the report for. Multiple occurances accepted')
@click.pass_context
def report(ctx,stage):
    """Opens the Vivado HLS report for the chosen build stages."""
    for report in stage:
        open_report(ctx,report)
