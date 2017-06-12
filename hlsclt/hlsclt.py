#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A Vivado HLS Command Line Helper tool

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import os
import sys
import shutil
import argparse
from glob import glob
import contextlib

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

### Support Functions ###
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

def get_vars_from_file(filename):
    import imp
    try:
        with open(filename) as f:
            config = imp.load_source('config', '', f)
        return config
    except OSError:
        print("Error: No hls_config.py found, please create a config file for your project. For an example config file please see the 'examples' folder within the hlsclt install directory.")
        sys.exit()

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

def just_loop_on(input):
  if isinstance(input, str):
    yield input
  else:
    try:
      for item in input:
        yield item
    except TypeError:
      yield input

def main():
    # Set up default config dictionary
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

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Helper tool for using Vivado HLS through the command line. If no arguments are specified then a default run is executed which includes C simulation, C synthesis, Cosimulation and export for both Vivado IP Catalog and System Generator. If any of the run options are specified then only those specified are performed.")
    parser.add_argument("-clean", help="remove all Vivado HLS generated files", action="store_true")
    parser.add_argument("-keep", help="keep all previous solution and generate a new one", action="store_true")
    parser.add_argument("-csim", help="perform C simulation stage", action="store_true")
    parser.add_argument("-syn", help="perform C synthesis stage", action="store_true")
    cosim_group = parser.add_mutually_exclusive_group()
    cosim_group.add_argument("-cosim", help="perform cosimulation", action="store_true")
    cosim_group.add_argument("-cosim_debug", help="perform cosimulation with debug logging", action="store_true")
    export_ip_group = parser.add_mutually_exclusive_group()
    export_ip_group.add_argument("-export_ip", help="perform export for Vivado IP Catalog", action="store_true")
    export_ip_group.add_argument("-evaluate_ip", help="perform export for Vivado IP Catalog with build to place and route", action="store_true")
    export_dsp_group = parser.add_mutually_exclusive_group()
    export_dsp_group.add_argument("-export_dsp", help="perform export for System Generator", action="store_true")
    export_dsp_group.add_argument("-evaluate_dsp", help="perform export for System Generator with build to place and route", action="store_true")
    args = parser.parse_args()

    # Load project specifics from local config file and add to config dict
    config_loaded = get_vars_from_file('hls_config.py')
    errors = []
    parse_config_vars(config_loaded, config, errors)
    if len(errors) != 0:
        for err in errors:
            print(err)
        print("Config Errors, exiting...")
        sys.exit()

    # Check for clean argument
    if args.clean:
        if len(sys.argv) > 2:
            print("Warning: The 'Clean' option is exclusive. All other arguments will be ignored.")
        if try_delete(config["project_name"]) + try_delete("run_hls.tcl") + try_delete("vivado_hls.log") == 3:
            print("Warning: Nothing to remove!")
        else:
            print("Cleaned up generated files.")
        sys.exit()

    # Write out TCL file
    file = open("run_hls.tcl","w")
    file.write("open_project " + config["project_name"] + "\n")
    file.write("set_top " + config["top_level_function_name"] + "\n")
    for src_file in config["src_files"]:
        file.write("add_files " + config["src_dir_name"] + "/" + src_file + "\n")
    for tb_file in config["tb_files"]:
        file.write("add_files -tb " + config["tb_dir_name"] + "/" + tb_file + "\n")
    if args.keep:
        paths = glob(config["project_name"] + "/solution*/")
        solution_num = len(paths) + 1
        if solution_num == 1:
            file.write("open_solution -reset \"solution1\"" + "\n")
        else:
            file.write("open_solution -reset \"solution" + str(solution_num) + "\"" + "\n")
    else:
        file.write("open_solution \"solution1\"" + "\n")
    file.write("set_part \{" + config["part_name"] + "\}" + "\n")
    file.write("create_clock -period " + config["clock_period"] + " -name default" + "\n")

    if not(args.csim or args.syn or args.cosim or args.cosim_debug or args.export_ip or args.export_dsp or args.evaluate_ip or args.evaluate_dsp):
        file.write("csim_design -clean" + "\n")
        file.write("csynth_design" + "\n")
        file.write("cosim_design -O -rtl " + config["language"] + "\n")
        file.write("export_design -format ip_catalog" + "\n")
        file.write("export_design -format sysgen" + "\n")
        file.write("exit" + "\n")
    else:
        if args.csim:
            file.write("csim_design -clean" + "\n")
        if args.syn:
            file.write("csynth_design" + "\n")
        if args.cosim:
            for language in just_loop_on(config["language"]):
                file.write("cosim_design -O -rtl " + language + "\n")
        if args.cosim_debug:
            for language in just_loop_on(config["language"]):
                file.write("cosim_design -rtl " + language + " -trace_level all" + "\n")
        if args.export_dsp:
            file.write("export_design -format ip_catalog" + "\n")
        if args.export_ip:
            file.write("export_design -format sysgen" + "\n")
        if args.evaluate_dsp:
            for language in just_loop_on(config["language"]):
                file.write("export_design -format ip_catalog -evaluate " + language + "\n")
        if args.evaluate_ip:
            for language in just_loop_on(config["language"]):
                file.write("export_design -format sysgen -evaluate " + language + "\n")
    file.write("exit")
    file.close()

    # Call the Vivado HLS process
    os.system("vivado_hls -f run_hls.tcl")

if __name__ == "__main__": main()
