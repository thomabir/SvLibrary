`timescale 10ns / 1ns
// CPOL 0: sclk idles low
// CPHA 0: data is valid on sclk leading edge
// MSB first

module SpiController #(
    parameter CLOCK_DIVIDE = 2,  // factor by which to divide clk_i to get sclk_o
    parameter FRAME_WIDTH = 32  // length in bits of a single SPI transfer
) (
    input clk_i,  // FPGA clock
    input reset_i,  // reset
    input start_i,  // start the transaction
    output is_idle_o,  // 1 if in idle state

    // SPI signals
    output spi_sclk_o,  // SCLK = clk_i / (2 * CLOCK_DIVIDE)
    output spi_mosi_o,  // MOSI
    input spi_miso_i,  // MISO
    output spi_cs_o,  // /CS

    // FPGA data
    output unsigned [FRAME_WIDTH-1:0] data_o,  // received data
    input unsigned [FRAME_WIDTH-1:0] data_i  // data to send
);

    parameter COUNTER_WIDTH = $clog2(FRAME_WIDTH) + 1;

    typedef enum logic [4:0] {
        IDLE,  // wait for start_i = 1
        CS_DOWN,  // put the /CS line to 0
        CLK_LEAD,  // leading edge of the clock
        CLK_TRAIL,  // trailing edge of the clock
        DONE  // wait for the start signal to go to 0
    } state_e;

    typedef struct packed {
        state_e state;
        logic [COUNTER_WIDTH-1:0] bit_counter;  // 5 bit wide -> 32 bit message width
        logic [5:0] clk_divider;

        // data used for rx/tx
        logic [FRAME_WIDTH-1:0] data_rx;
        logic [FRAME_WIDTH-1:0] data_tx;

        // data, final
        logic signed [FRAME_WIDTH-1:0] data_rx_final;
    } state_t;

    state_t state_d;
    state_t state_q;

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            state_q.state <= IDLE;
            state_q.bit_counter <= 0;
            state_q.clk_divider <= 0;
            state_q.data_rx <= 0;
            state_q.data_tx <= 0;
            state_q.data_rx_final <= 0;
        end
        else begin
            state_q <= state_d;
        end
    end  // always_ff

    always_comb begin
        state_d = state_q;

        case (state_q.state)

            // wait for start_i
            IDLE: begin
                state_d.bit_counter = COUNTER_WIDTH'(FRAME_WIDTH);
                state_d.clk_divider = CLOCK_DIVIDE;
                state_d.data_tx = data_i;  // fix the data to transmit
                if (start_i) state_d.state = CS_DOWN;
            end

            // set /CS low, prepare first bit to write
            CS_DOWN: begin
                if (state_q.clk_divider > 0) begin  // stay in CS_DOWN
                    state_d.clk_divider = state_q.clk_divider - 1;
                end
                else begin  // go to next state
                    state_d.clk_divider = CLOCK_DIVIDE;
                    state_d.state = CLK_LEAD;
                end
            end

            // leading edge of the clock
            CLK_LEAD: begin
                state_d.data_rx[state_q.bit_counter-1] = spi_miso_i;  // CPHA = 0: read data on leading edge

                if (state_q.clk_divider > 0) begin  // stay in CLK_LEAD
                    state_d.clk_divider = state_q.clk_divider - 1;
                end
                else begin  // go to next state
                    state_d.clk_divider = CLOCK_DIVIDE;
                    state_d.state = CLK_TRAIL;
                    state_d.bit_counter = state_q.bit_counter - 1;  // prepare tx data at trailing edge
                end
            end

            // trailing edge of the clock
            CLK_TRAIL: begin

                if (state_q.bit_counter == 0) begin
                    state_d.state = DONE;
                end
                else if (state_q.clk_divider == 0) begin  // do another read/write
                    state_d.state = CLK_LEAD;
                    state_d.clk_divider = CLOCK_DIVIDE;
                end
                else begin
                    state_d.clk_divider = state_q.clk_divider - 1;
                end
            end

            // wait for the start signal to clear and store the result
            DONE: begin
                state_d.data_rx_final = state_q.data_rx;
                state_d.state = IDLE;
            end

            default: begin
                state_d.state = IDLE;
            end

        endcase

    end  // always_comb


    // output signals
    assign spi_mosi_o = state_q.data_tx[state_q.bit_counter - 1] & (!spi_cs_o) & (state_q.bit_counter > 0);
    assign spi_sclk_o = (state_q.state == CLK_LEAD);
    assign spi_cs_o = ((state_q.state == IDLE) | (state_q.state == DONE));

    assign is_idle_o = (state_q.state == IDLE);
    assign data_o = state_q.data_rx_final;

endmodule
