open_project proj_simple_adder
set_top simple_adder
add_files src/dut.h
add_files src/dut.cpp
add_files -tb tb/testbench.cpp
open_solution "solution1"
set_part xc7z020clg484-1
create_clock -period 10 -name default
csim_design -clean
exit
