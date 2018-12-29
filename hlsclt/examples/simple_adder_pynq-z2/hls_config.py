# Config file for Simple Adder Vivado HLS project

# project_name = "adder"
top_level_function_name = "simple_adder"
#src_dir_name = "src"
#tb_dir_name = "tb"
# const_dir_name = "const"
src_files = ["dut.h","dut.cpp"]
tb_files = ["testbench.cpp"]
const_files = ["pynq-z2_v1.0.xdc"]
# part_name = "xc7z020clg484-1"
part_name = "xc7z020clg400-1" # PYNQ-Z2 part number
clock_period = "10"
language = "vhdl"
#compiler = ""
#cflags = ""
