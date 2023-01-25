"""Contains tests for the System Verilog modules controlling the AD7771 ADC

To run the tests, run `make`. To clean up the output of the simulator, run `make clean`.
"""
import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge

np.random.seed(0)


async def read_single_message(dut, msg):
    """Simulates the ADC sending a 64 bit message, reading it with AD7771_DoutReader, and checking the result."""

    # variables to check whether the transmission was successful
    ch1mask = int("0000000011111111111111111111111100000000000000000000000000000000", 2)
    ch2mask = int("0000000000000000000000000000000000000000111111111111111111111111", 2)
    expect_ch1 = (msg & ch1mask) >> 32  # bits from 32 to 55
    expect_ch2 = (msg & ch2mask) >> 0  # bits from 0 to 23

    dut.din.value = 0

    # start the transmission: drdy goes low, then high, then low again
    dut.drdy.value = 0
    await RisingEdge(dut.dclk)
    dut.drdy.value = 1
    await RisingEdge(dut.dclk)
    dut.drdy.value = 0

    # read the message
    for i in range(64):
        # din is the ith bit from the front
        dut.din.value = (msg >> (63 - i)) & 1

        await RisingEdge(dut.dclk)

    await FallingEdge(dut.clk_i)  # wait for the state machine to finish
    await FallingEdge(dut.clk_i)

    assert expect_ch1 == dut.ch1_o.value, f"Wrong data received: received {dut.ch1_o}, but expected {expect_ch1}"
    assert expect_ch2 == dut.ch2_o.value, f"Wrong data received: received {dut.ch2_o}, but expected {expect_ch2}"


@cocotb.test()  # pylint: disable=E1120
async def read_test(dut):
    """Set up the testbench for AD7771_DoutReader.sv and run the tests."""

    # set up the clocks
    clock = Clock(dut.clk_i, 20, units="ns")  # The system clock is 50 MHz = 20 ns
    adc_clock = Clock(dut.dclk, 126, units="ns")  # The adc clock is 8 MHz = 125 ns

    # start the clocks
    cocotb.start_soon(clock.start())
    cocotb.start_soon(adc_clock.start())

    # synchronize with the clock
    await FallingEdge(dut.clk_i)

    # reset the module
    dut.reset_i.value = 1
    await FallingEdge(dut.clk_i)
    dut.reset_i.value = 0
    await FallingEdge(dut.clk_i)

    # set up random test messages
    # ===========================
    # A message sent by the ADC consists of 64 bits:
    # - the first 8 bits are the cyclic redundancy check bits (not tested here),
    # - the next 24 bits are the data from channel 1,
    # - the next 8 bits are again cyclic redundancy check bits (not tested here),
    # - and the last 24 bits are the data from channel 2

    n_test = 10
    crc = "10101010"  # fake cyclic redundancy check (CRC) bits

    # chx_msgs contains random integers from 0 to the maximum value
    ch1_msgs = np.random.randint(low=0, high=2**24 - 1, size=n_test)
    ch2_msgs = np.random.randint(low=0, high=2**24 - 1, size=n_test)

    for ch1_msg, ch2_msg in zip(ch1_msgs, ch2_msgs):
        # convert the messages to binary strings, 24 bits long
        ch1_msg = bin(ch1_msg)[2:].zfill(24)
        ch2_msg = bin(ch2_msg)[2:].zfill(24)

        # concatenate the message strings and convert to a 64 bit integer
        msg_str = crc + ch1_msg + crc + ch2_msg
        msg = int(msg_str, 2)

        # send the message and check if the result is correct
        await read_single_message(dut, msg)
