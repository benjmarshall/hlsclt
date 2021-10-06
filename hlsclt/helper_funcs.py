# -*- coding: utf-8 -*-
""" Helper functions for the HLSCLT Command Line Tool.

Copyright (c) 2017 Ben Marshall
"""

import os
from click.shell_completion import CompletionItem
from pyaml import yaml
from .classes import Error, ConfigError
from .config import decode_and_map, decode_one_of, decode_choice, decode_default
from .config import decode_int, decode_list, decode_string, decode_const, decode_obj


def load_config(file):
    """
    Function to load the configuration from a file.
    """
    config_file = read_config_file(file)
    config = get_config_parser()(file.name, config_file)
    # Context sensitive analysis
    if isinstance(config, Error):
        raise config
    for file in config.src_files:
        file.path = os.path.join(config.src_dir_name, file.path)
    for file in config.tb_files:
        file.path = os.path.join(config.tb_dir_name, file.path)
    try:
        set_active_solution(config, config.solution)
    except ConfigError:
        # The specified solution is not in the solutions list
        # append a default solution with its name
        config.solutions.append(
            decode_solution()("", {"name": config.solution}))
        set_active_solution(config, config.solution)
    for solution in config.solutions:
        # Inherit defaults from project
        if not solution.top_level_function_name:
            solution.top_level_function_name =\
                config.top_level_function_name

    del config.tb_dir_name
    del config.src_dir_name
    return config


def set_active_solution(config, set_solution):
    for solution in config.solutions:
        if set_solution == solution.name:
            config.solution = set_solution
            config.active_solution = solution
            break
    else:
        raise ConfigError([Error("Solution '%s' not found in solutions: %s"
                                 % (config.solution,
                                    list(map(lambda s: s.name,
                                             config.solutions))))])


def complete_solution(ctx, param, incomplete):
    try:
        # Search for config_file in parent context, return [] if not found
        while ctx:
            if 'config_file' in ctx.params:
                break
            ctx = ctx.parent
        else:
            return []
        config = load_config(ctx.params['config_file'])

        def mk_completion_item(name):
            help = "default" if name == config.active_solution.name else ""
            return CompletionItem(name, help=help)

        return list(map(lambda name: mk_completion_item(name),
                        filter(lambda name: name.startswith(incomplete),
                        map(lambda sol: sol.name,
                            config.solutions))))
    except Exception:
        return []


def get_config_parser():

    default_proj_name = decode_default("proj_%s" % os.path.relpath(".", ".."))

    return decode_obj({
        "project_name":
            decode_one_of(decode_string, default_proj_name),
        "top_level_function_name":
            decode_string,
        "src_dir_name":
            decode_one_of(decode_string, decode_default("src/")),
        "tb_dir_name":
            decode_one_of(decode_string, decode_default("tb/")),
        "src_files":
            decode_one_of(decode_source_list(), decode_default([])),
        "tb_files":
            decode_one_of(decode_source_list(), decode_default([])),
        "compiler":
            decode_one_of(decode_choice("gcc", "clang"), decode_default("gcc")),
        "cflags":
            decode_one_of(decode_string, decode_default("")),
        "tb_cflags":
            decode_one_of(decode_string, decode_default("-Wno-unknown-pragmas")),
        "part_name":
            decode_string,
        "clock_period":
            decode_int,
        "language":
            decode_one_of(decode_choice("vhdl", "verilog"),
                         decode_default("vhdl")),
        "solution":
            decode_one_of(decode_string, decode_default("sol_default")),
        "solutions":
            decode_one_of(decode_list(decode_solution()),
                         decode_and_map(decode_const(decode_solution()("", {})),
                                       lambda sol: [sol])),
    })


def decode_solution():
    return decode_obj({
        "name":
            decode_one_of(decode_string, decode_default("sol_default")),
        "top_level_function_name":
            decode_one_of(decode_string, decode_default(None)),
        "directives":
            decode_one_of(decode_and_map(decode_string, lambda s: [s]),
                         decode_list(decode_string),
                         decode_default([])),
        "source":
            decode_one_of(decode_and_map(decode_string, lambda s: [s]),
                         decode_list(decode_string),
                         decode_default([])),
    })


def decode_source_list():
    def add_empty_flags(path):
        return decode_obj({'path': decode_string,
                          'cflags': decode_const('')})('', {'path': path,
                                                           'cflags': ""})
    simple_source_file = decode_and_map(decode_string, add_empty_flags)
    source_and_flags = decode_obj({
        'path': decode_string,
        'cflags': decode_one_of(decode_string, decode_const(""))
    })
    return decode_list(decode_one_of(simple_source_file, source_and_flags))


def read_config_file(file):
    """
    Read configuration values from config file,
        overwriting the default ones
    """
    try:
        file_content = "".join(file.readlines())
        return yaml.safe_load(file_content)
    except (OSError, IOError):
        raise Error("Error: No hls_config.json found, "
                    + "please create a config file for your project."
                    + "For an example config file please see the 'examples'"
                    + "folder within the hlsclt install directory.")


def create_solution(project_name, solution):
    path = project_name
    if not os.path.exists(path):
        os.mkdir(path)
    path = os.path.join(path, solution)
    if not os.path.exists(path):
        os.mkdir(path)
