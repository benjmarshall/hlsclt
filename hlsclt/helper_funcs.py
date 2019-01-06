# -*- coding: utf-8 -*-
""" Helper functions for the HLSCLT Command Line Tool.

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click
import os
import imp
from glob import glob
from .classes import *

### Function Definitions ###
# Function to generate the default config dicttionary
def generate_default_config():
    config = {
        "project_name" : "proj_" + os.path.relpath(".",".."),
        "top_level_function_name" : "",
        "src_dir_name" : "src",
        "tb_dir_name" : "tb",
        "cflags": "",
        "src_files" : "",
        "compiler": "",
        "tb_files" : "",
        "part_name" : "",
        "clock_period" : "",
        "language" : "vhdl",
    }
    return config

# Function to read in the config from a local file and generate a config structure.
def get_vars_from_file(filename):
    try:
        with click.open_file(filename) as f:
            config = imp.load_source('config', '', f)
        return config
    except (OSError, IOError):
        click.echo("Error: No hls_config.py found, please create a config file for your project. For an example config file please see the 'examples' folder within the hlsclt install directory.")
        raise click.Abort()

# Funtion to parse a loaded config structure and overwrite the config dictionary defaults.
def parse_config_vars(config_loaded, config, errors):
    config_loaded_dict = dict((name, getattr(config_loaded, name)) for name in dir(config_loaded) if not name.startswith('__'))
    config_loaded_set = set(config_loaded_dict)
    config_set = set(config)
    options_defined = config_loaded_set.intersection(config_set)
    del_list = [];
    for name in config:
        # Catch optional config entries which don't need defaults
        if str(name) == "compiler" or str(name) == "cflags":
            if str(name) not in options_defined:
                del_list.append(name)
            else:
                config[name] = config_loaded_dict[name]
        elif str(name) in options_defined:
            config[name] = config_loaded_dict[name]
            try:
                if not config[name]:
                    raise ConfigError("Error: " + name + " is not defined in config file. No default exists, please define a value in the config file.")
            except ConfigError as err:
                errors.append(err)
                continue
    for name in del_list:
        del config[name]

# Function to find the highest solution number within a HLS project.
def find_solution_num(ctx):
    config = ctx.obj.config
    # Seach for solution folders
    paths = glob(config["project_name"] + "/solution*/")
    solution_num = len(paths)
    # First solution is always 1.
    if solution_num == 0:
        solution_num = 1;
    else:
        # Only if this isn't the first solution
        # If keep argument is specified we are starting a new solution.
        try:
            if ctx.params["keep"]:
                solution_num = solution_num + 1
        except KeyError:
            pass
    return solution_num
