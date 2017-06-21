# -*- coding: utf-8 -*-
""" Class definitions for the HLSCLT Command Line Tool.

Copyright (c) 2017 Ben Marshall
"""

# Generic error class
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

# Specific error class for local config file errors
class ConfigError(Error):
    """Exception raised for options not defined in config.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

# Class to hold application specific info within the Click context.
class hlsclt_internal_object(object):
    def __init__(self, config={}, solution_num=1, file=None, syn_command_present=False):
        self.config = config
        self.solution_num = solution_num
        self.file=file
        self.syn_command_present = syn_command_present
