# -*- coding: utf-8 -*-
""" Report subcommands for HLSCLT.

Copyright (c) 2017 Ben Marshall
"""

# Imports
import click
import os
import subprocess
from hlsclt.helper_funcs import list_solutions


# Supporting Function
# Function to check if project exists
def check_for_project(ctx):
    config = ctx.obj.config
    if not os.path.isdir(config.project_name):
        click.echo("Error: Can't find a project folder"
                   + "have you run a build process yet?")
        raise click.Abort()


# Function for opening reports.
def open_report(ctx, report):
    config = ctx.obj.config
    sol_path = os.path.join(config.project_name, config.solution)
    report_files = []
    if report == 'csim':
        report_files.append(["csim", "report",
                             "%s_csim.log" % config.top_level_function_name])
    elif report == 'syn':
        report_files.append(["syn", "report",
                             "%s_csynth.rpt" % config.top_level_function_name])
    elif report == 'cosim':
        report_files.append(["sim", "report",
                             "%s_cosim.rpt" % config.top_level_function_name])
        report_files.append(["sim", "report", config.language,
                             "%s.log" % config.top_level_function_name])
    elif report == 'export':
        report_files.append(["impl", "report", config.language,
                             "%s_export.rpt" % config.top_level_function_name])

    # Prepend common solution path and join the path
    report_files = map(lambda path: os.path.join(sol_path, *path),
                       report_files)

    for file in report_files:
        return_val = subprocess.call('xdg-open' + 'file',
                                     stdout=os.devnull, stderr=os.devnull)
        if return_val != 0:
            click.echo(("Error: Looks like the %s report doesn't exist"
                        + "for project: %s, solution: %s. "
                        + "Make sure you have run that build stage.")
                       % (report, config.project_name, config.solution))


# Function for opening the HLS GUI
def open_project_in_gui(ctx):
    config = ctx.obj.config
    subprocess.Popen(["vivado_hls", "-p", config.project_name])


# Function for gathering the project status
def gather_project_status(ctx):
    config = ctx.obj.config
    project_status = []
    # Pull details from csim report
    try:
        sim_path = os.path.join(config.project_name, config.solution,
                                "csim", "report",
                                "%s_csim.log" % config.top_level_function_name)
        with click.open_file(sim_path, "r") as f:
            # Pass/Fail info is always in the second last
            # line of the csim report
            status_line = f.readlines()[-2]
            if "0 errors" in status_line.lower():
                project_status.append("csim_pass")
            elif "fail" in status_line.lower():
                project_status.append("csim_fail")
            else:
                project_status.append("csim_done")
        f.close()
    except (OSError, IOError):
        pass
    # Pull setails from csynth report
    syn_path = os.path.join(config.project_name, config.solution,
                            "syn", "report",
                            "%s_csynth.rpt" % config.top_level_function_name)
    if os.path.isfile(syn_path):
        project_status.append('syn_done')
    # Pull details from cosim report
    csm_path = os.path.join(config.project_name, config.solution,
                            "cosim", "report",
                            "%s_csynth.rpt" % config.top_level_function_name)
    try:
        with click.open_file(csm_path) as f:
            # search through cosim report to find out pass/fail status
            # for each language
            for line in f:
                if config["language"] in line.lower():
                    if "pass" in line.lower():
                        project_status.append('cosim_pass')
                    elif "fail" in line.lower():
                        project_status.append('cosim_fail')
            project_status.append('cosim_done')
        f.close()
    except (OSError, IOError):
        pass
    except Exception:
        pass
    # Pull details from implementation directory,
    # first the presence of an export...
    iip_path = os.path.join(config.project_name, config.solution,
                            "impl", "ip")
    if os.path.isdir(iip_path):
        project_status.append('export_ip_done')
    isg_path = os.path.join(config.project_name, config.solution,
                            "cosim", "report")
    if os.path.isdir(isg_path):
        project_status.append('export_sysgen_done')
    # ... then the presence of a Vivado evaluate run
    imp_path = os.path.join(config.project_name, config.solution,
                            "impl", "report", config.language,
                            "%s_export.rpt" % config.top_level_function_name)
    if os.path.isfile(imp_path):
        project_status.append('evaluate_done')
    return project_status


# Function for printing out the project status
def print_project_status(ctx, stats):
    config = ctx.obj.config
    project_status = gather_project_status(ctx)
    # Print out a 'pretty' message showing project status,
    # first up some project details
    click.secho("Project Details", bold=True)
    click.echo("  Project Name: " + config.project_name)
    click.echo("  Solution Folder: '%s'" % config.solution)
    click.echo("  Language Choice: " + config.language)
    # And now details about what builds have been run/are passing.
    click.secho("Build Status", bold=True)

    def get_msg(prefix):
        msg = "Not Run"
        fg = 'yellow'
        if "%s_pass" % prefix in project_status:
            msg = "Pass"
            fg = 'green'
        elif "%s_fail" % prefix in project_status:
            msg = "Fail"
            fg = 'red'
        elif "%s_done" % prefix in project_status:
            msg = "Run (can't get status)"
            fg = 'yellow'
        else:
            msg = "Not Run"
            fg = 'yellow'
        return click.style(msg, fg=fg)

    click.echo("  C Simulation: " + get_msg("csim"))
    click.echo("  C Synthesis:  " + get_msg("syn"))
    click.echo("  Cosimulation: " + get_msg("cosim"))
    click.echo("  Export:")
    click.echo("    IP Catalog:        " + get_msg("export_ip"))
    click.echo("    System Generator:  " + get_msg("export_sysgen"))
    click.echo("    Export Evaluation: " + get_msg("export_evaluation"))

    # Provide a stats summary of obtained accross solutions
    def csm_path(solution):
        return os.path.join(config.project_name, solution,
                            "cosim", "report",
                            "%s_csynth.rpt" % config.top_level_function_name)
    if stats:
        click.secho("Solutions", bold=True)
        for solution in list_solutions:
            # Fetch the information directly from the report, if possible
            try:
                with click.open_file(csm_path) as f:
                    click.echo(click.style("  Solution ", fg="magenta")
                               + "%s :" % solution)
                    report_content = f.readlines()
                    ap_clk_line = report_content[22]
                    ap_clk_line_elements = [x.strip()
                                            for x in ap_clk_line.split('|')]
                    clk_target = ap_clk_line_elements[2]
                    clk_estimated = ap_clk_line_elements[3]
                    clk_uncertainty = ap_clk_line_elements[4]
                    click.echo("    clock:")
                    click.echo("     - Target: " + clk_target + " ns")
                    click.echo("     - Estimated: "
                               + (click.style(clk_estimated, fg='green')
                                  if float(clk_estimated) < float(clk_target)
                                  else click.style(clk_estimated, fg='red'))
                               + " ns")
                    click.echo("     - Uncertainty: "
                               + click.style(clk_uncertainty, fg='yellow')
                               + " ns")

                    # Fetch line 32, latency in cycles
                    #       |  686|  686|  686|  686|   none  |
                    summary_line = report_content[31]
                    summary_line_elements = [x.strip()
                                             for x in summary_line.split('|')]
                    # latency_min = summary_line_elements[1]
                    # latency_max = summary_line_elements[2]
                    interval_min = float(summary_line_elements[3]) + 1
                    # Get the max interval (and sum 1 since a 0 interval/cycle
                    # means at least requires 1)
                    interval_max = float(summary_line_elements[4]) + 1
                    click.echo("    period (time to execute:)):")
                    click.echo("     - min: "
                               + str(float(clk_estimated)*interval_min)
                               + " ns")
                    click.echo("     - min (cycles): "
                               + str(int(interval_min))
                               + " cycles")
                    click.echo("     - max: "
                               + click.style(str((float(clk_estimated)
                                                  + float(clk_uncertainty))
                                                 * interval_max), fg="cyan")
                               + " ns")
                    click.echo("     - max (cycles): "
                               + str(int(interval_max))
                               + " cycles")

                    # if "0 errors" in status_line.lower():
                    #     project_status.append("csim_pass")
                    # elif "fail" in status_line.lower():
                    #     project_status.append("csim_fail")
                    # else:
                    #     project_status.append("csim_done")
                f.close()
            except IOError:
                pass


# Click Command Definitions
# Report Command
@click.command('report', short_help='Open reports.')
@click.option('-s', '--stage', required=True, multiple=True,
              type=click.Choice(['csim', 'syn', 'cosim', 'export']),
              help="Which build stage to open the report for."
                    + "Multiple occurences accepted")
@click.pass_context
def report(ctx, stage):
    """Opens the Vivado HLS report for the chosen build stages."""
    check_for_project(ctx)
    for report in stage:
        open_report(ctx, report)


@click.command('open_gui',
               short_help='Open the Vivado HLS GUI and load the project.')
@click.pass_context
def open_gui(ctx):
    """Opens the Vivado HLS GUI and loads the project."""
    check_for_project(ctx)
    open_project_in_gui(ctx)


@click.command('status', short_help='Print out the current project status.')
@click.option('-s', '--stats', is_flag=True,
              help='Include a summary of stats for each solution.')
@click.pass_context
def status(ctx, stats):
    """Prints out a message detailing the current project status."""
    check_for_project(ctx)
    print_project_status(ctx, stats)
