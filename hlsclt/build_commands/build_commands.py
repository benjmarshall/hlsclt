# -*- coding: utf-8 -*-
""" Build related subcommands for HLSCLT.

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click
import os
import subprocess
from hlsclt.helper_funcs import *
from hlsclt.report_commands.report_commands import open_report
import shutil
import platform
import hlsclt
OS=platform.system()

### Supporting Functions ###
# Function to generate the 'pre-amble' within the HLS Tcl build script.
def do_start_build_stuff(ctx):
    config = ctx.obj.config
    #print("config=",config)
    solution_num = ctx.obj.solution_num
    exts=('jpg', 'png','h')
    try:
        file = click.open_file("run_hls.tcl","w")
        file.write("open_project " + config["project_name"] + "\n")
        file.write("set_top " + config["top_level_function_name"] + "\n")
        if config.get("cflags","") != "":
            cf = " -cflags \"%s\"" % config["cflags"]
        else:
            cf = ""
        for src_file in config["src_files"]:
            f, ext = os.path.splitext(src_file)
            cf_temp = cf if ext[1:].lower() not in exts else ""
            file.write("add_files " + config["src_dir_name"] + "/" + src_file + cf_temp + "\n")

        if config.get("cflags_tb","") != "":
            cf_tb = " -cflags \"%s\"" % config["cflags_tb"]
        else:
            cf_tb = ""
        for tb_file in config["tb_files"]:
            f, ext = os.path.splitext(tb_file)
            cf_tb_temp = cf_tb if ext[1:].lower() not in exts else ""
            add_str="add_files -tb " + config["tb_dir_name"] + "/" + tb_file + cf_tb_temp + "\n"
            #print("add_str=",add_str)
            #print("cf_tb_temp=", cf_tb_temp)
            file.write(add_str)

        if ctx.params['keep']:
            file.write("open_solution -reset \"solution" + str(solution_num) + "\"" + "\n")
        else:
            file.write("open_solution \"solution" + str(solution_num) + "\"" + "\n")
        file.write("set_part " + config["part_name"] + "\n")
        file.write("create_clock -period " + config["clock_period"] + " -name default" + "\n")
        return file
    except (OSError, IOError):
        click.echo("Woah! Couldn't create a Tcl run file in the current folder!")
        raise click.Abort()

# Function to write a default build into the HLS Tcl build script.
def do_default_build(ctx):
    config = ctx.obj.config
    file = ctx.obj.file
    file.write("csim_design -clean" + (" -compiler clang" if config.get("compiler","") == "clang" else "") + " \n")
    file.write("csynth_design" + "\n")
    file.write("cosim_design -O -rtl " + config["language"] + "\n")
    file.write("export_design -format ip_catalog" + "\n")
    file.write("export_design -format sysgen" + "\n")

# Function which defines the main actions of the 'csim' command.
def do_csim_stuff(ctx):
    file = ctx.obj.file
    config = ctx.obj.config
    file.write("csim_design -clean" + (" -compiler clang" if config.get("compiler","") == "clang" else "") + "\n")

# Function which defines the main actions of the 'syn' command.
def do_syn_stuff(ctx):
    file = ctx.obj.file
    file.write("csynth_design" + "\n")

# Function to perform a search for existing c synthesis results in a specified hls project and solution.
def check_for_syn_results(proj_name, solution_num, top_level_function_name):
    return_val = False
    try:
        with click.open_file(proj_name + "/solution" + str(solution_num) + "/syn/report/" + top_level_function_name + "_csynth.rpt"):
            return_val = True
    except (OSError, IOError):
        pass
    return return_val

# Function to check is C synthesis is going to be required but may have been forgorgotten by the user.
def syn_lookahead_check(ctx):
    config = ctx.obj.config
    solution_num = ctx.obj.solution_num
    file = ctx.obj.file
    if (not ctx.obj.syn_command_present) and (not check_for_syn_results(config["project_name"], solution_num, config["top_level_function_name"])):
        if click.confirm("C Synthesis has not yet been run but is required for the process(es) you have selected.\nWould you like to add it to this run?", default=True):
            click.echo("Adding csynth option.")
            file.write("csynth_design" + "\n")
        else:
            click.echo("Ok, watch out for missing synthesis errors!")

# Function which defines the main actions of the 'cosim' command.
def do_cosim_stuff(ctx,debug):
    config = ctx.obj.config
    file = ctx.obj.file
    if debug:
        file.write("cosim_design -rtl " + config["language"] + " -trace_level all" + "\n")
    else:
        file.write("cosim_design -O -rtl " + config["language"] + "\n")

# Function which defines the main actions of the 'export' command.
def do_export_stuff(ctx,type,evaluate):
    config = ctx.obj.config
    file = ctx.obj.file
    if evaluate:
        if "ip" in type:
            file.write("export_design -format ip_catalog -evaluate " + config["language"] + "\n")
        if "sysgen" in type:
            file.write("export_design -format sysgen -evaluate " + config["language"] + "\n")
    else:
        if "ip" in type:
            file.write("export_design -format ip_catalog" + "\n")
        if "sysgen" in type:
            file.write("export_design -format sysgen" + "\n")

# Function which defines the actions that occur after a HLS build.
def do_end_build_stuff(ctx,sub_command_returns,report):
    # Copy the src/ files as well as the config file to keep track of the changes over solutions
    config = ctx.obj.config
    solution_num = ctx.obj.solution_num
    click.echo("Copying the source and config files to solution"+str(solution_num))
    destiny = config["project_name"] + "/solution" + str(solution_num)
    destiny_src = destiny + "/src"
    destiny_config = destiny + "/hls_config.py"
    # If we are overwriting an existing solution delete the source directory first.
    if ctx.params['keep'] == 0:
        shutil.rmtree(destiny_src, ignore_errors=True)
    shutil.copytree(config["src_dir_name"], destiny_src)
    shutil.copyfile("hls_config.py", destiny_config)

    # Check for reporting flag
    if report:
        if not sub_command_returns:
            # Must be on the default run, add all stages manually
            sub_command_returns = ['csim','syn','cosim','export']
        for report in sub_command_returns:
            open_report(ctx,report)

### Click Command Definitions ###
# Build group entry point
@click.group(chain=True, invoke_without_command=True, short_help='Run HLS build stages.')
@click.option('-k','--keep', is_flag=True, help='Preserves existing solutions and creates a new one.')
@click.option('-r','--report', is_flag=True, help='Open build reports when finished.')
@click.pass_context
def build(ctx,keep,report):
    """Runs the Vivado HLS tool and executes the specified build stages."""
    ctx.obj.solution_num = find_solution_num(ctx)
    ctx.obj.file = do_start_build_stuff(ctx)
    pass

# Callback which executes when all specified build subcommands have been finished.
@build.resultcallback()
@click.pass_context
def build_end_callback(ctx,sub_command_returns,keep,report):
    config = ctx.obj.config
    # Catch the case where no subcommands have been issued and offer a default build
    if not sub_command_returns:
        if click.confirm("No build stages specified, would you like to run a default sequence using all the build stages?", abort=True):
            do_default_build(ctx)
    ctx.obj.file.write("exit" + "\n")
    ctx.obj.file.close()
    # Call the Vivado HLS process
    print("vivado_hls is now launching in %s!"%OS)
    vivado_hls="vivado_hls"
    if OS=="Windows":
        returncode = subprocess.call([vivado_hls, "-f", "run_hls.tcl"],shell=True)
    else:
        # CANNOT USE SHELL=TRUE IN LINUX
        if  OS=="Linux":
            if config.get("vivado_hls_version","") != "":
                vivado_hls2=os.path.join("/","tools","Xilinx","Vivado",config["vivado_hls_version"],"bin","vivado_hls")
            else:
                vivado_hls2=vivado_hls
        print("vivado_hls=%s"%vivado_hls2)
        returncode = subprocess.call([vivado_hls2, "-f", "run_hls.tcl"])
    # Check return status of the HLS process.
    if returncode < 0:
        raise click.Abort()
    elif returncode > 0:
        click.echo("Warning: HLS Process returned an error, skipping report opening!")
        raise click.Abort()
    else:
        do_end_build_stuff(ctx,sub_command_returns,report)

# csim subcommand
@build.command('csim')
@click.pass_context
def csim(ctx):
    """Runs the Vivado HLS C simulation stage."""
    do_csim_stuff(ctx)
    return 'csim'

# syn subcommand
@build.command('syn')
@click.pass_context
def syn(ctx):
    """Runs the Vivado HLS C synthesis stage."""
    do_syn_stuff(ctx)
    ctx.obj.syn_command_present = True
    return 'syn'

# cosim subcommand
@build.command('cosim')
@click.option('-d', '--debug', is_flag=True, help='Turns off compile optimisations and enables logging for cosim.')
@click.pass_context
def cosim(ctx,debug):
    """Runs the Vivado HLS cosimulation stage."""
    syn_lookahead_check(ctx)
    do_cosim_stuff(ctx,debug)
    return 'cosim'

# export subcommand
@build.command('export')
@click.option('-t', '--type',  required=True, multiple=True, type=click.Choice(['ip','sysgen']), help='Specify an export type, Vivado IP Catalog or System Generator. Accepts multiple occurences.')
@click.option('-e', '--evaluate', is_flag=True, help='Runs Vivado synthesis and place and route for the generated export.')
@click.pass_context
def export(ctx, type, evaluate):
    """Runs the Vivado HLS export stage."""
    syn_lookahead_check(ctx)
    do_export_stuff(ctx,type,evaluate)
    return 'export'
