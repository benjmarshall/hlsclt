#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A Vivado HLS Command Line Helper tool

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click
from ._version import __version__
import os
import sys
import shutil
import argparse
from glob import glob
import contextlib
from distutils.util import strtobool

### Class definitions ###
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ConfigError(Error):
    """Exception raised for options not defined in config.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

class hlsclt_internal_object(object):
    def __init__(self, config={}, solution_num=1, file=None, syn_command_present=False):
        self.config = config
        self.solution_num = solution_num
        self.file=file
        self.syn_command_present = syn_command_present

### New Click Stuff ###
def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()

def generate_default_config():
    config = {
        "project_name" : "proj_" + os.path.relpath(".",".."),
        "top_level_function_name" : "",
        "src_dir_name" : "src",
        "tb_dir_name" : "tb",
        "src_files" : "",
        "tb_files" : "",
        "part_name" : "",
        "clock_period" : "",
        "language" : "vhdl",
    }
    return config

def get_vars_from_file(filename):
    import imp
    try:
        with click.open_file(filename) as f:
            config = imp.load_source('config', '', f)
        return config
    except OSError:
        print("Error: No hls_config.py found, please create a config file for your project. For an example config file please see the 'examples' folder within the hlsclt install directory.")
        raise click.Abort()

def parse_config_vars(config_loaded, config, errors):
    config_loaded_dict = dict((name, getattr(config_loaded, name)) for name in dir(config_loaded) if not name.startswith('__'))
    config_loaded_set = set(config_loaded_dict)
    config_set = set(config)
    options_defined = config_loaded_set.intersection(config_set)
    for name in config:
        if str(name) in options_defined:
            config[name] = config_loaded_dict[name]
        try:
            if not config[name]:
                raise ConfigError("Error: " + name + " is not defined in config file. No default exists, please define a value in the config file.")
        except ConfigError as err:
            errors.append(err)
            continue

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

def clean_up_generated_files(obj):
        config = obj.config
        if try_delete(config["project_name"]) + try_delete("run_hls.tcl") + try_delete("vivado_hls.log") == 3:
            click.echo("Warning: Nothing to remove!")
        else:
            click.echo("Cleaned up generated files.")

def find_solution_num(ctx):
    config = ctx.obj.config
    # Find solution_num
    paths = glob(config["project_name"] + "/solution*/")
    solution_num = len(paths)
    if solution_num == 0:
        solution_num = 1;
    elif ctx.params["keep"]:
        solution_num = solution_num + 1
    return solution_num

def do_start_build_stuff(ctx):
    config = ctx.obj.config
    solution_num = ctx.obj.solution_num
    try:
        file = click.open_file("run_hls.tcl","w")
        file.write("open_project " + config["project_name"] + "\n")
        file.write("set_top " + config["top_level_function_name"] + "\n")
        for src_file in config["src_files"]:
            file.write("add_files " + config["src_dir_name"] + "/" + src_file + "\n")
        for tb_file in config["tb_files"]:
            file.write("add_files -tb " + config["tb_dir_name"] + "/" + tb_file + "\n")
        if ctx.params['keep']:
            file.write("open_solution -reset \"solution" + str(solution_num) + "\"" + "\n")
        else:
            file.write("open_solution \"solution" + str(solution_num) + "\"" + "\n")
        file.write("set_part \{" + config["part_name"] + "\}" + "\n")
        file.write("create_clock -period " + config["clock_period"] + " -name default" + "\n")
        return file
    except OSError:
        click.echo("Woah! Couldn't create a Tcl run file in the current folder!")
        raise click.Abort()

def do_default_build(ctx):
    config = ctx.obj.config
    file = ctx.obj.file
    file.write("csim_design -clean" + "\n")
    file.write("csynth_design" + "\n")
    file.write("cosim_design -O -rtl " + config["language"] + "\n")
    file.write("export_design -format ip_catalog" + "\n")
    file.write("export_design -format sysgen" + "\n")

def do_csim_stuff(ctx):
    file = ctx.obj.file
    file.write("csim_design -clean" + "\n")

def do_syn_stuff(ctx):
    file = ctx.obj.file
    file.write("csynth_design" + "\n")

def check_for_syn_results(proj_name, solution_num, top_level_function_name):
    return_val = False
    try:
        with click.open_file(proj_name + "/solution" + str(solution_num) + "/syn/report/" + top_level_function_name + "_csynth.rpt"):
            return_val = True
    except OSError:
        pass
    return return_val

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

def do_cosim_stuff(ctx,debug):
    config = ctx.obj.config
    file = ctx.obj.file
    if debug:
        for language in just_loop_on(config["language"]):
            file.write("cosim_design -rtl " + language + " -trace_level all" + "\n")
    else:
        for language in just_loop_on(config["language"]):
            file.write("cosim_design -O -rtl " + language + "\n")

def just_loop_on(input):
  if isinstance(input, str):
    yield input
  else:
    try:
      for item in input:
        yield item
    except TypeError:
      yield input

def do_export_stuff(ctx,type,evaluate):
    config = ctx.obj.config
    file = ctx.obj.file
    if evaluate:
        if "ip" in type:
            for language in just_loop_on(config["language"]):
                file.write("export_design -format ip_catalog -evaluate " + language + "\n")
        if "sysgen" in type:
            for language in just_loop_on(config["language"]):
                file.write("export_design -format sysgen -evaluate " + language + "\n")
    else:
        if "ip" in type:
            file.write("export_design -format ip_catalog" + "\n")
        if "sysgen" in type:
            file.write("export_design -format sysgen" + "\n")

@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """Helper tool for using Vivado HLS through the command line. If no arguments are specified then a default run is executed which includes C simulation, C synthesis, Cosimulation and export for both Vivado IP Catalog and System Generator. If any of the run options are specified then only those specified are performed."""
    config = generate_default_config();
    config_loaded = get_vars_from_file('hls_config.py')
    errors = []
    parse_config_vars(config_loaded, config, errors)
    if len(errors) != 0:
        for err in errors:
            print(err)
        print("Config Errors, exiting...")
        raise click.Abort()
    obj = hlsclt_internal_object(config)
    ctx.obj = obj
    pass

@cli.command('clean',short_help='Remove generated files.')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to remove all generated files?',
              help='Force quiet removal.')
@click.pass_obj
def clean(obj):
    """Removes all Vivado HLS generated files and the generated Tcl build script."""
    clean_up_generated_files(obj)

@cli.group(chain=True, invoke_without_command=True, short_help='Run HLS build stages.')
@click.option('-k','--keep', is_flag=True, help='Preserves existing solutions and creates a new one.')
@click.option('-r','--report', is_flag=True, help='Open build reports when finished.')
@click.pass_context
def build(ctx,keep,report):
    """Runs the Vivado HLS tool and executes the specified build stages."""
    ctx.obj.solution_num = find_solution_num(ctx)
    ctx.obj.file = do_start_build_stuff(ctx)
    pass

@build.resultcallback()
@click.pass_context
def build_end_callback(ctx,sub_command_returns,keep,report):
    if not any(sub_command_returns):
        if click.confirm("No build stages specified, would you like to run a default sequence using all the build stages?", abort=True):
            do_default_build(ctx)
    ctx.obj.file.write("exit" + "\n")
    ctx.obj.file.close()
    # Call the Vivado HLS process
    os.system("vivado_hls -f run_hls.tcl")

@build.command('csim')
@click.pass_context
def csim(ctx):
    """Runs the Vivado HLS C simulation stage."""
    do_csim_stuff(ctx)
    return True

@build.command('syn')
@click.pass_context
def syn(ctx):
    """Runs the Vivado HLS C synthesis stage."""
    do_syn_stuff(ctx)
    ctx.obj.syn_command_present = True
    return True

@build.command('cosim')
@click.option('-d', '--debug', is_flag=True, help='Turns off compile optimisations and enables logging for cosim.')
@click.pass_context
def cosim(ctx,debug):
    """Runs the Vivado HLS cosimulation stage."""
    syn_lookahead_check(ctx)
    do_cosim_stuff(ctx,debug)
    return True

@build.command('export')
@click.option('-t', '--type',  required=True, multiple=True, type=click.Choice(['ip','sysgen']), help='Specify an export type, Vivado IP Catalog or System Generator. Accepts multiple occurances.')
@click.option('-e', '--evaluate', is_flag=True, help='Runs Vivado synthesis and place and route for the generated export.')
@click.pass_context
def export(ctx, type, evaluate):
    """Runs the Vivado HLS export stage."""
    syn_lookahead_check(ctx)
    do_export_stuff(ctx,type,evaluate)
    return True

@cli.command('report',short_help='Open reports.')
def report():
    """Opens the Vivado HLS report for the chosen build stages."""
    click.echo("Report Mode")
