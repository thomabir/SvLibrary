// Read output data from the AD7771 via the DOUT Data interface (ADC is master, FPGA is slave)
// (This is the only way to read all 8 ADCs simultaneously at 128 kS/s)

module DoutReader (
    input clk_i,  // FPGA clock
    input reset_i,  // reset

    // ADC pins
    input drdy,  // /DRDY
    input dclk,  // DCLK
    input din,  // DIN

    // ADC readings, in twos' complement
    output [23:0] ch1_o,  // channel 1
    output [23:0] ch2_o,  // channel 2

    output tick_o  // tick whenever chx_o is updated
);

    typedef enum logic [4:0] {
        WAIT_DRDY,
        WAIT_DLCK,
        WRITE_DATA,
        FINALISE_DATA
    } state_e;

    typedef struct packed {
        state_e state;
        logic [5:0] i;  // counts from 63 down to 0 while filling up in_data
        logic drdy_1;  // /DRDY, one clk_i cycle ago
        logic drdy_2;  // /DRDY, two clk_i cycles ago
        logic dclk_1;  // DCLK, one clk_i cycle ago
        logic dclk_2;  // DCLK, two clk_i cycles ago
        logic [63:0] in_data;  // message read from the ADC
        logic [63:0] final_data;
        logic tick;  // tick whenever final_data is updated
    } state_t;

    state_t state_d;
    state_t state_q;

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            state_q.state <= WAIT_DRDY;
            state_q.i <= 63;
            state_q.in_data <= 0;
            state_q.final_data <= 0;
            state_q.drdy_1 <= 0;
            state_q.drdy_2 <= 0;
            state_q.dclk_1 <= 0;
            state_q.dclk_2 <= 0;
            state_q.tick <= 0;
        end
        else begin
            state_q <= state_d;  // default
            state_q.drdy_2 <= state_d.drdy_1;
            state_q.drdy_1 <= drdy;
            state_q.dclk_2 <= state_d.dclk_1;
            state_q.dclk_1 <= dclk;
        end
    end  // always_ff

    always_comb begin
        state_d = state_q;  // default

        case (state_q.state)

            // wait for DRDY to go low
            WAIT_DRDY: begin
                // reset values
                state_d.i = 63;
                state_d.in_data = 0;
                state_d.tick = 0;

                // if DRDY goes low, go to next state
                if (state_q.drdy_2 && !state_q.drdy_1) begin
                    state_d.state = WAIT_DLCK;
                end

            end

            // wait for DCLK to go low
            WAIT_DLCK: begin
                // if DCLK goes low, go to next state
                if (state_q.dclk_2 && !state_q.dclk_1) begin
                    state_d.state = WRITE_DATA;
                end
            end

            // write din into the ith bit of in_data
            WRITE_DATA: begin
                state_d.in_data[state_q.i] = din;
                state_d.i = state_q.i - 1;

                // if all bits have been written, go to next state
                if (state_q.i == 0) begin
                    state_d.state = FINALISE_DATA;
                end  // otherwise, wait for DCLK to go low again
                else begin
                    state_d.state = WAIT_DLCK;
                end
            end

            // split up in_data into ch1_o and ch2_o
            FINALISE_DATA: begin
                state_d.final_data = state_q.in_data;
                state_d.state = WAIT_DRDY;
                state_d.tick = 1;
            end

            // default
            default: begin
                state_d.state = WAIT_DRDY;
            end


        endcase
    end  // always_comb


    // output signals
    assign ch1_o = state_q.final_data[55:32];
    assign ch2_o = state_q.final_data[23:0];
    assign tick_o = state_q.tick;

endmodule
