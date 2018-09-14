# Vivado HLS Command Line Tool (hlsclt)

A Vivado HLS Command Line Helper Tool.

Supports a command line driven development process, which increases the performance of the HLS tool and aids compatibility with source control tools, in order achieve an increase in productivity.

## Features
- Flexibly execute any of the Vivado HLS build stages
- Open build reports
- Clean up generated files
- View complete project status
- Open Vivado HLS GUI with project loaded

## Requirements
- Python 2 or 3
    - Tested with and 2.7.5 and 3.6.1
- Vivado HLS
  - Tested with Vivado HLS 2017.1

## Install
```Shell
pip install hlsclt
```
Depends on [Click](https://pypi.python.org/pypi/click) which will be installed automatically by pip.

## Usage
### Quickstart
This tool is intended to aid a command line driven development process for Vivado HLS. Whilst the tool is designed to be flexible, certain guidelines should be followed. A top level project folder should contain your HLS source files (or folders) and a 'hls_config.py' file which specifies some of the required configuration for a HLS project (device, clock speed etc).

A recommended directory structure is as follows:

- my_project_name
  - src
    - dut.cpp
    - dut.h
  - tb
    - testbench.cpp
  - hls_config.py

An example project structure and hls_config.py can be found in the [examples](hlsclt/examples) directory. A full guide for setting a config.py can be seen in the [Project Config](#project-configuration) section.

The tool should be invoked from within the project folder, i.e. :
```Shell
cd my_project_name
hlsclt build csim
```

The tool will read in the configuration from your 'hls_config.py' file and invoke Vivado HLS to perform the chosen build stages.

All of the tools commands and options can be seen by using the '--help' argument:

```
[ben@localhost]$ hlsclt --help
Usage: hlsclt [OPTIONS] COMMAND [ARGS]...

  Helper tool for using Vivado HLS through the command line. If no arguments
  are specified then a default run is executed which includes C simulation,
  C synthesis, Cosimulation and export for both Vivado IP Catalog and System
  Generator. If any of the run options are specified then only those
  specified are performed.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  build     Run HLS build stages.
  clean     Remove generated files.
  open_gui  Open the Vivado HLS GUI and load the project.
  report    Open reports.
  status    Print out the current project status.
```

### Nested Commands
The tool is built using the concept of 'nested' commands (like git for example), where the main command 'hlsclt' has a group of subcommands, some of which in turn have subcommands. The 'status' command is a simple example of single level of nesting:

```
[ben@localhost]$ hlsclt status
Project Details
  Project Name: proj_simple_adder
  Number of solutions generated: 1
  Latest Solution Folder: 'proj_simple_adder/solution1'
  Language Choice: vhdl
Build Status
  C Simulation: Pass
  C Synthesis:  Not Run
  Cosimulation: Not Run
  Export:
    IP Catalog:        Not Run
    System Generator:  Not Run
    Export Evaluation: Not Run
```

The build subcommand is slightly more complex than the other top-level commands. Nested subcommands under the build command can be chained in order to perform multiple HLS build stages, each with their own options:

```
[ben@localhost]$ hlsclt build csim syn cosim -d
```

In this example the tool will launch the HLS process to run a C simulation, followed by C Synthesis, and finally a cosimulation with debugging enabled so that we can view the waveforms of the cosimulation at a later point.

Each command or subcommand has it's own help option which gives specific information about the command and how to use it. For example the export subcomand:
```
[ben@localhost]$ hlsclt build export --help
Usage: hlsclt build export [OPTIONS]

  Runs the Vivado HLS export stage.

Options:
  -t, --type [ip|sysgen]  Specify an export type, Vivado IP Catalog or System
                          Generator. Accepts multiple occurrences.  [required]
  -e, --evaluate          Runs Vivado synthesis and place and route for the
                          generated export.
  --help                  Show this message and exit.
```

### Project Configuration
Each Vivado HLS project requires a 'config.py' file in order to use hlsclt. This file contains all of the information required by Vivado HLS and hlsclt to perform build operations for your project. The file uses basic python syntax to specify the configuration in a parsable format. The full list of available configuration options is shown below:

|Configuration Item | Variable Name         | Valid Options                  | Required |
|-------------------|-----------------------|--------------------------------|----------|
|Project Name       |project_name           |Any valid directory name        |No (Default is name of the containing project folder prepended with 'proj_')       |
|Function Name      |top_level_function_name|String which match function name|Yes       |
|Source Files Dir   |src_dir_name           |Name of directory where source files are located, relative to the project folder|No (Default is 'src')|
|Testbench Files Dir|tb_dir_name            |Name of directory where testbench files are located, relative to the project folder|No (Default is 'tb')|
|Source Files       |src_files              |A list of source files required, located within the Source Files directory|Yes|
|Testbench Files    |tb_files               |A list of testbench files required, located within the Testbench Files directory|Yes|
|Device String      |part_name              |A device string as used by Vivado HLS (see examples)|Yes|
|Clock Period       |clock_period           |A value in nanoseconds input as a string, e.g. "10"|Yes|
|HDL Language       |language               |Either "vhdl" or "verilog"      |No (Default is "vhdl")|
|Compiler           |Compiler               |Either "gcc" or "clang"         |No (HLS defaults to gcc)|
|Compiler Options   |cflags                 |Any flag for GCC (e.g. --std=c++11)|No|


Here is an example file taken from the [simple_adder](hlsclt/examples/simple_adder) example shipped with the tool (note that some of the optional items have been commented out in order to use the defaults):

```python
# Config file for Simple Adder Vivado HLS project

#project_name = "optional_project_name_here"
top_level_function_name = "simple_adder"
#src_dir_name = "src"
#tb_dir_name = "tb"
# cflags = ""
src_files = ["dut.h","dut.cpp"]
tb_files = ["testbench.cpp"]
part_name = "xc7z020clg484-1"
clock_period = "10"
language = "vhdl"
```

## License

See [LICENSE](LICENSE)

## Bugs/Issues
If you have any issues or find a bug please first search the [open issues](https://github.com/benjmarshall/hlsclt/issues) on github and then submit a new issue ticket.  
