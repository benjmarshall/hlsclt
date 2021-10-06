# -*- coding: utf-8 -*-
""" Helper functions for the HLSCLT Command Line Tool.

Copyright (c) 2017 Ben Marshall
"""

import os
from click.shell_completion import CompletionItem
from pyaml import yaml
from .classes import Error, ConfigError
from .config import parse_and_map, parse_one_of, parse_choice, parse_default
from .config import parse_int, parse_list, parse_string, parse_const, parse_obj


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
            parse_solution()("", {"name": config.solution}))
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

    default_proj_name = parse_default("proj_%s" % os.path.relpath(".", ".."))

    return parse_obj({
        "project_name":
            parse_one_of(parse_string, default_proj_name),
        "top_level_function_name":
            parse_string,
        "src_dir_name":
            parse_one_of(parse_string, parse_default("src/")),
        "tb_dir_name":
            parse_one_of(parse_string, parse_default("tb/")),
        "src_files":
            parse_one_of(parse_source_list(), parse_default([])),
        "tb_files":
            parse_one_of(parse_source_list(), parse_default([])),
        "compiler":
            parse_one_of(parse_choice("gcc", "clang"), parse_default("gcc")),
        "cflags":
            parse_one_of(parse_string, parse_default("")),
        "tb_cflags":
            parse_one_of(parse_string, parse_default("-Wno-unknown-pragmas")),
        "part_name":
            parse_string,
        "clock_period":
            parse_int,
        "language":
            parse_one_of(parse_choice("vhdl", "verilog"),
                         parse_default("vhdl")),
        "solution":
            parse_one_of(parse_string, parse_default("sol_default")),
        "solutions":
            parse_one_of(parse_list(parse_solution()),
                         parse_and_map(parse_const(parse_solution()("", {})),
                                       lambda sol: [sol])),
    })


def parse_solution():
    return parse_obj({
        "name":
            parse_one_of(parse_string, parse_default("sol_default")),
        "top_level_function_name":
            parse_one_of(parse_string, parse_default(None)),
        "directives":
            parse_one_of(parse_and_map(parse_string, lambda s: [s]),
                         parse_list(parse_string),
                         parse_default([])),
        "source":
            parse_one_of(parse_and_map(parse_string, lambda s: [s]),
                         parse_list(parse_string),
                         parse_default([])),
    })


def parse_source_list():
    def add_empty_flags(path):
        return parse_obj({'path': parse_string,
                          'cflags': parse_const('')})('', {'path': path,
                                                           'cflags': ""})
    simple_source_file = parse_and_map(parse_string, add_empty_flags)
    source_and_flags = parse_obj({
        'path': parse_string,
        'cflags': parse_one_of(parse_string, parse_const(""))
    })
    return parse_list(parse_one_of(simple_source_file, source_and_flags))


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
