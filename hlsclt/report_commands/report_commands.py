# -*- coding: utf-8 -*-
""" Report subcommands for HLSCLT.

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click
import os
import subprocess
from glob import glob
from hlsclt.helper_funcs import find_solution_num

### Supporting Functions ###
# Function to check if project exists
def check_for_project(ctx):
    config = ctx.obj.config
    if not glob(config["project_name"]):
        click.echo("Error: Can't find a project folder have you run a build process yet?")
        raise click.Abort()

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
        report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/sim/report/" + config["language"] + "/" + config["top_level_function_name"] + ".log")
    elif report == 'export':
        report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/impl/report/" + config["language"] + "/" + config["top_level_function_name"] + "_export.rpt")
    for file in report_files:
        return_val = os.system('xdg-open ' + file + ' >/dev/null 2>&1')
        if return_val != 0:
            click.echo("Error: Looks like the " + report + " report doesn't exist for project: " + config["project_name"] + ", solution number: " + str(solution_num) + ". Make sure you have run that build stage.")

# Function for opening the HLS GUI
def open_project_in_gui(ctx):
    config = ctx.obj.config
    hls_process = subprocess.Popen(["vivado_hls", "-p", config["project_name"]])

# Function for gathering the project status
def gather_project_status(ctx):
    config = ctx.obj.config
    solution_num = ctx.obj.solution_num
    project_status = []
    # Pull details from csim report
    try:
        with click.open_file(config["project_name"] + "/solution" + str(solution_num) + "/csim/report/" + config["top_level_function_name"] + "_csim.log","r") as f:
            # Pass/Fail info is always in the second last line of the csim report
            status_line = f.readlines()[-2]
            if "0 errors" in status_line.lower():
                project_status.append("csim_pass")
            elif "fail" in status_line.lower():
                project_status.append("csim_fail")
            else:
                project_status.append("csim_done")
        f.close()
    except OSError:
        pass
    # Pull setails from csynth report
    if os.path.isfile(config["project_name"] + "/solution" + str(solution_num) + "/syn/report/" + config["top_level_function_name"] + "_csynth.rpt"):
        project_status.append('syn_done')
    # Pull details from cosim report
    try:
        with click.open_file(config["project_name"] + "/solution" + str(solution_num) + "/sim/report/" + config["top_level_function_name"] + "_cosim.rpt","r") as f:
            # search through cosim report to find out pass/fail status for each language
            for line in f:
                if config["language"] in line.lower():
                    if "pass" in line.lower():
                        project_status.append('cosim_pass')
                    elif "fail" in line.lower():
                        project_status.append('cosim_fail')
            project_status.append('cosim_done')
        f.close()
    except OSError:
        pass
    # Pull details from implementation directory, first the presence of an export...
    if os.path.isdir(config["project_name"] + "/solution" + str(solution_num) + "/impl/ip"):
        project_status.append('export_ip_done')
    if os.path.isdir(config["project_name"] + "/solution" + str(solution_num) + "/impl/sysgen"):
        project_status.append('export_sysgen_done')
    # ... then the presence of a Vivado evaluate run
    if os.path.isfile(config["project_name"] + "/solution" + str(solution_num) + "/impl/report/" + config["language"] + "/" + config["top_level_function_name"] + "_export.rpt"):
        project_status.append('evaluate_done')
    return project_status

# Function for printing out the project status
def print_project_status(ctx):
    config = ctx.obj.config
    solution_num = ctx.obj.solution_num
    project_status = gather_project_status(ctx)
    # Print out a 'pretty' message showing project status, first up some project details
    click.secho("Project Details", bold=True)
    click.echo("  Project Name: " + config["project_name"])
    click.echo("  Number of solutions generated: " + str(solution_num))
    click.echo("  Latest Solution Folder: '" + config["project_name"] + "/solution" + str(solution_num) + "'")
    click.echo("  Language Choice: " + config["language"])
    # And now details about what builds have been run/are passing.
    # This section uses lots (too many!) 'conditional expressions' to embed formatting into the output.
    click.secho("Build Status", bold=True)
    click.echo("  C Simulation: " + (click.style("Pass", fg='green') if "csim_pass" in project_status else (click.style("Fail", fg='red') if "csim_fail" in project_status else (click.style("Run (Can't get status)", fg='yellow') if "csim_done" in project_status else click.style("Not Run", fg='yellow')))))
    click.echo("  C Synthesis:  " + (click.style("Run", fg='green') if "syn_done" in project_status else click.style("Not Run", fg='yellow')))
    click.echo("  Cosimulation: " + (click.style("Pass", fg='green') if "cosim_pass" in project_status else (click.style("Fail", fg='red') if "cosim_fail" in project_status else (click.style("Run (Can't get status)", fg='yellow') if "cosim_done" in project_status else click.style("Not Run", fg='yellow')))))
    click.echo("  Export:" )
    click.echo("    IP Catalog:        " + (click.style("Run", fg='green') if "export_ip_done" in project_status else click.style("Not Run", fg='yellow')))
    click.echo("    System Generator:  " + (click.style("Run", fg='green') if "export_sysgen_done" in project_status else click.style("Not Run", fg='yellow')))
    click.echo("    Export Evaluation: " + (click.style("Run", fg='green') if "evaluate_done" in project_status else click.style("Not Run", fg='yellow')))

### Click Command Definitions ###
# Report Command
@click.command('report', short_help='Open reports.')
@click.option('-s', '--stage', required=True, multiple=True,
                type=click.Choice(['csim','syn','cosim','export']),
                help='Which build stage to open the report for. Multiple occurences accepted')
@click.pass_context
def report(ctx,stage):
    """Opens the Vivado HLS report for the chosen build stages."""
    check_for_project(ctx)
    ctx.obj.solution_num = find_solution_num(ctx)
    for report in stage:
        open_report(ctx,report)

@click.command('open_gui', short_help='Open the Vivado HLS GUI and load the project.')
@click.pass_context
def open_gui(ctx):
    """Opens the Vivado HLS GUI and loads the project."""
    check_for_project(ctx)
    open_project_in_gui(ctx)

@click.command('status', short_help='Print out the current project status.')
@click.pass_context
def status(ctx):
    """Prints out a message detailing the current project status."""
    check_for_project(ctx)
    ctx.obj.solution_num = find_solution_num(ctx)
    print_project_status(ctx)
