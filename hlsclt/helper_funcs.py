# -*- coding: utf-8 -*-
""" Helper functions for the HLSCLT Command Line Tool.

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click
import os
import imp
from glob import glob

### Function Definitions ###
# Function to generate the default config dicttionary
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

# Function to read in the config from a local file and generate a config structure.
def get_vars_from_file(filename):
    try:
        with click.open_file(filename) as f:
            config = imp.load_source('config', '', f)
        return config
    except OSError:
        click.echo("Error: No hls_config.py found, please create a config file for your project. For an example config file please see the 'examples' folder within the hlsclt install directory.")
        raise click.Abort()

# Funtion to parse a loaded config structure and overwrite the config dictionary defaults.
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

# Function to find the highest solution number within a HLS project.
def find_solution_num(ctx):
    config = ctx.obj.config
    # Seach for solution folders
    paths = glob(config["project_name"] + "/solution*/")
    solution_num = len(paths)
    # First solution is always 1.
    if solution_num == 0:
        solution_num = 1;
    # If keep argument is specified we are starting a new solution.
    try:
        if ctx.params["keep"]:
            solution_num = solution_num + 1
    except KeyError:
        pass
    return solution_num
