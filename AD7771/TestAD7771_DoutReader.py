import cocotb
import numpy as np

from cgi import test
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb.triggers import RisingEdge
from cocotb.triggers import Timer

np.random.seed(0)


async def ReadSingleMessage(dut, msg):
    """
    Simulates sending a 64 bit msg from the ADC and reading it with DoutReader, then checks if the result is correct.
    """

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

    # might need to wait for another rising edge of dclk here, but I'm not sure. Look at verilator output.

    # read the message
    for i in range(64):
        # din is the ith bit from the front
        dut.din.value = (msg >> (63 - i)) & 1

        await RisingEdge(dut.dclk)

    await FallingEdge(dut.clk_i)  # wait for the state machine to finish
    await FallingEdge(dut.clk_i)

    assert (
        expect_ch1 == dut.ch1_o.value
    ), f"Wrong data received: received {dut.ch1_o}, but expected {expect_ch1}"
    assert (
        expect_ch2 == dut.ch2_o.value
    ), f"Wrong data received: received {dut.ch2_o}, but expected {expect_ch2}"


@cocotb.test()
async def ReadWriteTest(dut):

    # system clock of 20 ns, and a DCLK of 8 MHz = 125 ns
    clock = Clock(dut.clk_i, 20, units="ns")  # 20 ns = 50 MHz
    adc_clock = Clock(dut.dclk, 126, units="ns")  # 125 ns = 8 MHz
    cocotb.start_soon(clock.start())
    cocotb.start_soon(adc_clock.start())

    await FallingEdge(dut.clk_i)  # Synchronize with the clock

    # do a reset
    dut.reset_i.value = 1
    await FallingEdge(dut.clk_i)
    dut.reset_i.value = 0
    await FallingEdge(dut.clk_i)

    # Set up test messages
    n_test = 10
    crc = "10101010"  # cyclic redundancy check bits, I don't care about them
    ch1_msgs = np.random.randint(low=0, high=2**24 - 1, size=n_test)
    ch2_msgs = np.random.randint(low=0, high=2**24 - 1, size=n_test)

    for ch1_msg, ch2_msg in zip(ch1_msgs, ch2_msgs):

        # convert the messages to a 64 bit integer
        ch1_msg = bin(ch1_msg)[2:].zfill(24)
        ch2_msg = bin(ch2_msg)[2:].zfill(24)
        msg_str = crc + ch1_msg + crc + ch2_msg
        msg = int(msg_str, 2)

        # send the message and check if the result is correct
        await ReadSingleMessage(dut, msg)
