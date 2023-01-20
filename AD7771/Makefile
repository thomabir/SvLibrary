VERILOG_SOURCES = $(PWD)/AD7771_DoutReader.sv
TOPLEVEL=AD7771_DoutReader
MODULE=TestAD7771_DoutReader

export COCOTB_REDUCED_LOG_FMT = 1 # shorter lines in the terminal
SIM=verilator
COCOTB_HDL_TIMEPRECISION = 1ns

EXTRA_ARGS += --trace --trace-structs



include $(shell cocotb-config --makefiles)/Makefile.sim

clean ::
	rm -rf __pycache__
	rm -f results.xml