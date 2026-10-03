# Generic integer datapath interface contracts

Textbook, width-parameterized integer building blocks. Two's-complement where signed.
Widths listed are the instances exercised in the reference build; the contract is the
parameterized function, so any width is a valid competition target.

| Interface id | Block | Ports | Function | Notes |
|---|---|---|---|---|
| `q2_if.full_adder` | 1-bit full adder | `s, cout, a, b, cin` | {cout,s} = a + b + cin | n_bits=1. |
| `q2_if.rca` | Ripple-carry adder (N-bit) | `sum[N-1:0], cout, a[N-1:0], b[N-1:0], cin` | {cout,sum} = a + b + cin | Parameterized width N. Portal instances: N in {8,16,48,52}. The 48-bit instance is an explicit challenge target. |
| `q2_if.add_tree` | Adder reduction tree | `sum[W:0], x_0..x_{M-1}` | sum = x_0 + x_1 + ... + x_{M-1} | Portal instance: 32-way. |
| `q2_if.sub` | Integer subtractor (N-bit) | `d[N-1:0], bout, a[N-1:0], b[N-1:0]` | d = a - b (two's complement) | Portal instance: 32-bit. |
| `q2_if.inc` | Incrementer (N-bit) | `y[N-1:0], a[N-1:0]` | y = a + 1 | Portal instance: 32-bit. |
| `q2_if.barrel_shift` | Barrel shifter (N-bit) | `y[N-1:0], a[N-1:0], sh[log2N-1:0], dir` | y = (dir==L) ? a << sh : a >> sh | Combinational shift by any amount. Portal instances: left-32, left-64, right-64. |
| `q2_if.prio_enc` | Priority encoder (N-bit) | `idx[log2N-1:0], valid, a[N-1:0]` | idx = index of the leading one of a; valid = |a | Leading-one detector. Portal instances: N in {8,32,64}. |
| `q2_if.decoder` | One-hot decoder | `oh[2^K-1:0], sel[K-1:0], en` | oh = en ? (1 << sel) : 0 | Portal instance: 5->32 write decoder. |
| `q2_if.mux2_bus` | 2:1 bus multiplexer (N-bit) | `y[N-1:0], a[N-1:0], b[N-1:0], s` | y = s ? b : a | Datapath-width 2:1 select. |
| `q2_if.reg` | Register (N-bit) | `q[N-1:0], d[N-1:0], clk, en` | q <= en ? d : q at rising clk | Portal instance: 32-bit. |
| `q2_if.regfile` | Register file | `rd_data..., rd_addr..., wr_data, wr_addr, wr_en, clk` | Synchronous-write, combinational/registered-read multi-port register file | Portal instance: 32x32, multi-ported. Specify port count and read timing in your submission. |
| `q2_if.array_mul` | Array multiplier (NxN) | `p[2N-1:0], a[N-1:0], b[N-1:0]` | p = a * b (unsigned integer) | Portal instance: 24x24. |
