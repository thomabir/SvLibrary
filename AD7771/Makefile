VERILOG_SOURCES = $(PWD)/DoutReader.sv
TOPLEVEL=DoutReader
MODULE=test


SIM=verilator
COCOTB_HDL_TIMEPRECISION = 1ns

EXTRA_ARGS += --trace --trace-structs
export COCOTB_REDUCED_LOG_FMT = 1 # shorter lines in the terminal

include $(shell cocotb-config --makefiles)/Makefile.sim

clean ::
	rm -rf __pycache__
	rm -f results.xml
