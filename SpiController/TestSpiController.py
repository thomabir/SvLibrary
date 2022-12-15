from cgi import test
import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge
import numpy as np
np.random.seed(0)

async def ReadWriteSingleMessage(dut, data_tx, data_rx):
    """
    Write data_tx to the device and read data_rx from the device, then check both.
    """
    # set up the input signals and do a reset
    dut.data_i.value = data_tx
    dut.start_i.value = 0
    await FallingEdge(dut.clk_i)
    
    # start transmission
    dut.start_i.value = 1

    # variables to check whether the transmission was successful
    value_tx = 0 # transmitted data
    value_rx = 0 # received data

    # try to read the data and check if the result is correct:
    for i in range(32):
        await RisingEdge(dut.spi_sclk_o)

        # write bit of 
        if (dut.spi_mosi_o == 1):
            value_tx = value_tx + 2**(31 - i)

        dut.spi_miso_i.value = (data_rx >> (31-i)) & 1

    
    await RisingEdge(dut.spi_cs_o)
    dut.start_i.value = 0
    await Timer(40, "ns")

    value_rx = dut.data_o

    assert value_tx == data_tx, f"Wrong data sent: sent {value_tx}, but expected {data_tx}"
    assert value_rx == data_rx, f"Wrong data received: received {value_rx}, but expected {data_rx}"    
    

@cocotb.test()
async def ReadWriteTest(dut):

    clock = Clock(dut.clk_i, 20, units="ns")  # 20 ns = 50 MHz
    cocotb.start_soon(clock.start())

    await FallingEdge(dut.clk_i)  # Synchronize with the clock
    
    # do a reset:
    dut.reset_i.value = 1
    await FallingEdge(dut.clk_i)
    dut.reset_i.value = 0
    await FallingEdge(dut.clk_i)

    # write a zero, read 570
    await ReadWriteSingleMessage(dut, 0, 570)

    # write max
    await ReadWriteSingleMessage(dut, 2**32-1, 570)

    # read a zero
    await ReadWriteSingleMessage(dut, 570, 0)

    # read max
    await ReadWriteSingleMessage(dut, 570, 2**32-1)

    # read/write random integers
    n_test = 10
    values_tx = np.random.randint(low=0,high=2**32-1,size=n_test)
    values_rx = np.random.randint(low=0,high=2**32-1,size=n_test)

    for value_tx, value_rx in zip(values_tx, values_rx):
        await ReadWriteSingleMessage(dut, int(value_tx), int(value_rx))