# Vivado HLS Command Line Tool (hlsclt)
A Vivado HLS Command Line Helper Tool.

Current functionality includes flexibly executing the main Vivado HLS build stages and cleaning up generated files. Supports a command line driven development process.

## Requirements
Python 3 - tested with python 3.6.1

## Install
Easy installation:
```Shell
pip install hlsclt
```

Manual installation:
```Shell
git clone https://github.com/benjmarshall/hlsclt.git
sudo cp ./hlsclt/hlsclt/hlsclt.py /usr/local/bin/hlsclt
sudo chmod +x /usr/local.bin/hlsclt
```

## Usage
This tool is intended to aid command line driven development process for Vivado HLS. Whilst the tool is designed to be flexible, certain guidelines should be followed. A top level project folder should contain your HLS source files (or folders) and a 'hls_config.py' file which specifies some of the required configuration for a HLS project (device, clock speed etc).

A recommended directory structure is as follows:

- my_project_name
  - src
    - dut.cpp
    - dut.h
  - tb
    - testbench.cpp
  - hls_config.py

An example project structure and hls_config.py can be found in the [examples](hlsclt/examples) directory.

The tool should be invoked from within the project folder, i.e.:
```Shell
cd my_project_name
hlsclt -csim
```

The tool will read in the configuration from your 'hls_config.py' file and invoke Vivado HLS to perform the chosen build stages.

All of the tool options can be seen my using the '--help' argument:

```
[ben@localhost]$ hlsclt --help
usage: hlsclt [-h] [-clean] [-keep] [-csim] [-syn] [-cosim | -cosim_debug] [-export_ip | -evaluate_ip]
              [-export_dsp | -evaluate_dsp]

Helper tool for using Vivado HLS through the command line. If no arguments are specified then a default
run is executed which includes C simulation, C synthesis, Cosimulation and export for both Vivado IP
Catalog and System Generator. If any of the run options are specified then only those specified are
performed.

optional arguments:
  -h, --help     show this help message and exit
  -clean         remove all Vivado HLS generated files
  -keep          keep all previous solution and generate a new one
  -csim          perform C simulation stage
  -syn           perform C synthesis stage
  -cosim         perform cosimulation
  -cosim_debug   perform cosimulation with debug logging
  -export_ip     perform export for Vivado IP Catalog
  -evaluate_ip   perform export for Vivado IP Catalog with build to place and route
  -export_dsp    perform export for System Generator
  -evaluate_dsp  perform export for System Generator with build to place and route
```

## License

See [LICENSE](LICENSE)
