VERILOG_SOURCES = $(PWD)/SpiController.sv
TOPLEVEL=SpiController
MODULE=TestSpiController

SIM=verilator
COCOTB_HDL_TIMEPRECISION = 1ns

EXTRA_ARGS += --trace --trace-structs

include $(shell cocotb-config --makefiles)/Makefile.sim

clean ::
	rm -rf __pycache__
	rm -f results.xml
