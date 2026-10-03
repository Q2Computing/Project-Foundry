# sky130 PDK standard-cell interface contracts

The complete **sky130_fd_sc_hd** logic library as published by the open PDK (Apache-2.0).
Functions, ports, and sequential behavior are extracted directly from the PDK Liberty and
blackbox Verilog mounted in the reference flow, the gold-standard reference. Every cell
also carries the four standard power/bulk pins `VPWR, VGND, VPB, VNB`.

Physical, analog, clock-tree, isolation and fill cells (clk*, dly*, decap, diode, tap, conb,
isolation/low-power, fill, spare) are intentionally **not** listed: they are not
implement-a-better-one targets. Published here: 93 combinational gates and 30 sequential cells.

**Golden reference for validation:** each cell's own PDK functional Verilog. A competing
implementation is validated by logic-equivalence check against it (see `VERIFICATION.md`),
then measured by sky130 physical signoff for the leaderboard metric.

## Combinational (93)

| Interface id | Family | Ports | Function | Drives |
|---|---|---|---|---|
| `sky130_fd_sc_hd__a2111o` | AND-OR complex gate | X, A1, A2, B1, C1, D1 | `(A1&A2) | (B1) | (C1) | (D1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a2111oi` | AND-OR complex gate | Y, A1, A2, B1, C1, D1 | `(!A1&!B1&!C1&!D1) | (!A2&!B1&!C1&!D1)` | x0, x1, x2, x4 |
| `sky130_fd_sc_hd__a211o` | AND-OR complex gate | X, A1, A2, B1, C1 | `(A1&A2) | (B1) | (C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a211oi` | AND-OR complex gate | Y, A1, A2, B1, C1 | `(!A1&!B1&!C1) | (!A2&!B1&!C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a21bo` | AND-OR complex gate | X, A1, A2, B1_N | `(A1&A2) | (!B1_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a21boi` | AND-OR complex gate | Y, A1, A2, B1_N | `(!A1&B1_N) | (!A2&B1_N)` | x0, x1, x2, x4 |
| `sky130_fd_sc_hd__a21o` | AND-OR complex gate | X, A1, A2, B1 | `(A1&A2) | (B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a21oi` | AND-OR complex gate | Y, A1, A2, B1 | `(!A1&!B1) | (!A2&!B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a221o` | AND-OR complex gate | X, A1, A2, B1, B2, C1 | `(B1&B2) | (A1&A2) | (C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a221oi` | AND-OR complex gate | Y, A1, A2, B1, B2, C1 | `(!A1&!B1&!C1) | (!A1&!B2&!C1) | (!A2&!B1&!C1) | (!A2&!B2&!C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a222oi` | AND-OR complex gate | Y, A1, A2, B1, B2, C1, C2 | `(!A1&!B1&!C1) | (!A1&!B1&!C2) | (!A1&!B2&!C1) | (!A2&!B1&!C1) | (!A1&!B2&!C2) | (!A2&!B1&!C2) | (!A2&!B2&!C1) | (!A2&!B2&!C2)` | x1 |
| `sky130_fd_sc_hd__a22o` | AND-OR complex gate | X, A1, A2, B1, B2 | `(B1&B2) | (A1&A2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a22oi` | AND-OR complex gate | Y, A1, A2, B1, B2 | `(!A1&!B1) | (!A1&!B2) | (!A2&!B1) | (!A2&!B2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a2bb2o` | AND-OR complex gate | X, A1_N, A2_N, B1, B2 | `(B1&B2) | (!A1_N&!A2_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a2bb2oi` | AND-OR complex gate | Y, A1_N, A2_N, B1, B2 | `(A1_N&!B1) | (A1_N&!B2) | (A2_N&!B1) | (A2_N&!B2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a311o` | AND-OR complex gate | X, A1, A2, A3, B1, C1 | `(A1&A2&A3) | (B1) | (C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a311oi` | AND-OR complex gate | Y, A1, A2, A3, B1, C1 | `(!A1&!B1&!C1) | (!A2&!B1&!C1) | (!A3&!B1&!C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a31o` | AND-OR complex gate | X, A1, A2, A3, B1 | `(A1&A2&A3) | (B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a31oi` | AND-OR complex gate | Y, A1, A2, A3, B1 | `(!A1&!B1) | (!A2&!B1) | (!A3&!B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a32o` | AND-OR complex gate | X, A1, A2, A3, B1, B2 | `(A1&A2&A3) | (B1&B2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a32oi` | AND-OR complex gate | Y, A1, A2, A3, B1, B2 | `(!A1&!B1) | (!A1&!B2) | (!A2&!B1) | (!A3&!B1) | (!A2&!B2) | (!A3&!B2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a41o` | AND-OR complex gate | X, A1, A2, A3, A4, B1 | `(A1&A2&A3&A4) | (B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__a41oi` | AND-OR complex gate | Y, A1, A2, A3, A4, B1 | `(!A1&!B1) | (!A2&!B1) | (!A3&!B1) | (!A4&!B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__and2` | AND | X, A, B | `(A&B)` | x0, x1, x2, x4 |
| `sky130_fd_sc_hd__and2b` | AND | X, A_N, B | `(!A_N&B)` | x1, x2, x4 |
| `sky130_fd_sc_hd__and3` | AND | X, A, B, C | `(A&B&C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__and3b` | AND | X, A_N, B, C | `(!A_N&B&C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__and4` | AND | X, A, B, C, D | `(A&B&C&D)` | x1, x2, x4 |
| `sky130_fd_sc_hd__and4b` | AND | X, A_N, B, C, D | `(!A_N&B&C&D)` | x1, x2, x4 |
| `sky130_fd_sc_hd__and4bb` | AND | X, A_N, B_N, C, D | `(!A_N&!B_N&C&D)` | x1, x2, x4 |
| `sky130_fd_sc_hd__buf` | Buffer | X, A | `(A)` | x1, x2, x4, x6, x8, x12, x16 |
| `sky130_fd_sc_hd__bufbuf` | Buffer | X, A | `(A)` | x8, x16 |
| `sky130_fd_sc_hd__bufinv` | Buffer | Y, A | `(!A)` | x8, x16 |
| `sky130_fd_sc_hd__ebufn` | Tri-state buffer | Z, A, TE_B | `(A)` | x1, x2, x4, x8 |
| `sky130_fd_sc_hd__einvn` | Tri-state inverter | Z, A, TE_B | `(!A)` | x0, x1, x2, x4, x8 |
| `sky130_fd_sc_hd__einvp` | Tri-state inverter | Z, A, TE | `(!A)` | x1, x2, x4, x8 |
| `sky130_fd_sc_hd__fa` | Full adder | COUT, SUM, A, B, CIN | `(A&B) | (A&CIN) | (B&CIN)` | x1, x2, x4 |
| `sky130_fd_sc_hd__fah` | Full adder (carry) | COUT, SUM, A, B, CI | `(A&B) | (A&CI) | (B&CI)` | x1 |
| `sky130_fd_sc_hd__fahcin` | Full adder (carry) | COUT, SUM, A, B, CIN | `(A&!CIN) | (A&B) | (B&!CIN)` | x1 |
| `sky130_fd_sc_hd__fahcon` | Full adder (carry) | COUT_N, SUM, A, B, CI | `(!A&!CI) | (!A&!B) | (!B&!CI)` | x1 |
| `sky130_fd_sc_hd__ha` | Half adder | COUT, SUM, A, B | `(A&B)` | x1, x2, x4 |
| `sky130_fd_sc_hd__inv` | Inverter | Y, A | `(!A)` | x1, x2, x4, x6, x8, x12, x16 |
| `sky130_fd_sc_hd__maj3` | Majority | X, A, B, C | `(A&B) | (A&C) | (B&C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__mux2` | Multiplexer | X, A0, A1, S | `(A0&!S) | (A1&S)` | x1, x2, x4, x8 |
| `sky130_fd_sc_hd__mux2i` | Multiplexer | Y, A0, A1, S | `(!A0&!S) | (!A1&S)` | x1, x2, x4 |
| `sky130_fd_sc_hd__mux4` | Multiplexer | X, A0, A1, A2, A3, S0, S1 | `(A0&!S0&!S1) | (A1&S0&!S1) | (A2&!S0&S1) | (A3&S0&S1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nand2` | NAND | Y, A, B | `(!A) | (!B)` | x1, x2, x4, x8 |
| `sky130_fd_sc_hd__nand2b` | NAND | Y, A_N, B | `(A_N) | (!B)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nand3` | NAND | Y, A, B, C | `(!A) | (!B) | (!C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nand3b` | NAND | Y, A_N, B, C | `(A_N) | (!B) | (!C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nand4` | NAND | Y, A, B, C, D | `(!A) | (!B) | (!C) | (!D)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nand4b` | NAND | Y, A_N, B, C, D | `(A_N) | (!B) | (!C) | (!D)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nand4bb` | NAND | Y, A_N, B_N, C, D | `(A_N) | (B_N) | (!C) | (!D)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nor2` | NOR | Y, A, B | `(!A&!B)` | x1, x2, x4, x8 |
| `sky130_fd_sc_hd__nor2b` | NOR | Y, A, B_N | `(!A&B_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nor3` | NOR | Y, A, B, C | `(!A&!B&!C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nor3b` | NOR | Y, A, B, C_N | `(!A&!B&C_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nor4` | NOR | Y, A, B, C, D | `(!A&!B&!C&!D)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nor4b` | NOR | Y, A, B, C, D_N | `(!A&!B&!C&D_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nor4bb` | NOR | Y, A, B, C_N, D_N | `(!A&!B&C_N&D_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o2111a` | OR-AND complex gate | X, A1, A2, B1, C1, D1 | `(A1&B1&C1&D1) | (A2&B1&C1&D1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o2111ai` | OR-AND complex gate | Y, A1, A2, B1, C1, D1 | `(!A1&!A2) | (!B1) | (!C1) | (!D1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o211a` | OR-AND complex gate | X, A1, A2, B1, C1 | `(A1&B1&C1) | (A2&B1&C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o211ai` | OR-AND complex gate | Y, A1, A2, B1, C1 | `(!A1&!A2) | (!B1) | (!C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o21a` | OR-AND complex gate | X, A1, A2, B1 | `(A1&B1) | (A2&B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o21ai` | OR-AND complex gate | Y, A1, A2, B1 | `(!A1&!A2) | (!B1)` | x0, x1, x2, x4 |
| `sky130_fd_sc_hd__o21ba` | OR-AND complex gate | X, A1, A2, B1_N | `(A1&!B1_N) | (A2&!B1_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o21bai` | OR-AND complex gate | Y, A1, A2, B1_N | `(!A1&!A2) | (B1_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o221a` | OR-AND complex gate | X, A1, A2, B1, B2, C1 | `(A1&B1&C1) | (A2&B1&C1) | (A1&B2&C1) | (A2&B2&C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o221ai` | OR-AND complex gate | Y, A1, A2, B1, B2, C1 | `(!B1&!B2) | (!A1&!A2) | (!C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o22a` | OR-AND complex gate | X, A1, A2, B1, B2 | `(A1&B1) | (A2&B1) | (A1&B2) | (A2&B2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o22ai` | OR-AND complex gate | Y, A1, A2, B1, B2 | `(!B1&!B2) | (!A1&!A2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o2bb2a` | OR-AND complex gate | X, A1_N, A2_N, B1, B2 | `(!A1_N&B1) | (!A2_N&B1) | (!A1_N&B2) | (!A2_N&B2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o2bb2ai` | OR-AND complex gate | Y, A1_N, A2_N, B1, B2 | `(!B1&!B2) | (A1_N&A2_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o311a` | OR-AND complex gate | X, A1, A2, A3, B1, C1 | `(A1&B1&C1) | (A2&B1&C1) | (A3&B1&C1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o311ai` | OR-AND complex gate | Y, A1, A2, A3, B1, C1 | `(!A1&!A2&!A3) | (!B1) | (!C1)` | x0, x1, x2, x4 |
| `sky130_fd_sc_hd__o31a` | OR-AND complex gate | X, A1, A2, A3, B1 | `(A1&B1) | (A2&B1) | (A3&B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o31ai` | OR-AND complex gate | Y, A1, A2, A3, B1 | `(!A1&!A2&!A3) | (!B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o32a` | OR-AND complex gate | X, A1, A2, A3, B1, B2 | `(A1&B1) | (A1&B2) | (A2&B1) | (A3&B1) | (A2&B2) | (A3&B2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o32ai` | OR-AND complex gate | Y, A1, A2, A3, B1, B2 | `(!A1&!A2&!A3) | (!B1&!B2)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o41a` | OR-AND complex gate | X, A1, A2, A3, A4, B1 | `(A1&B1) | (A2&B1) | (A3&B1) | (A4&B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__o41ai` | OR-AND complex gate | Y, A1, A2, A3, A4, B1 | `(!A1&!A2&!A3&!A4) | (!B1)` | x1, x2, x4 |
| `sky130_fd_sc_hd__or2` | OR | X, A, B | `(A) | (B)` | x0, x1, x2, x4 |
| `sky130_fd_sc_hd__or2b` | OR | X, A, B_N | `(A) | (!B_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__or3` | OR | X, A, B, C | `(A) | (B) | (C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__or3b` | OR | X, A, B, C_N | `(A) | (B) | (!C_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__or4` | OR | X, A, B, C, D | `(A) | (B) | (C) | (D)` | x1, x2, x4 |
| `sky130_fd_sc_hd__or4b` | OR | X, A, B, C, D_N | `(A) | (B) | (C) | (!D_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__or4bb` | OR | X, A, B, C_N, D_N | `(A) | (B) | (!C_N) | (!D_N)` | x1, x2, x4 |
| `sky130_fd_sc_hd__xnor2` | XNOR | Y, A, B | `(!A&!B) | (A&B)` | x1, x2, x4 |
| `sky130_fd_sc_hd__xnor3` | XNOR | X, A, B, C | `(!A&!B&!C) | (A&B&!C) | (A&!B&C) | (!A&B&C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__xor2` | XOR | X, A, B | `(A&!B) | (!A&B)` | x1, x2, x4 |
| `sky130_fd_sc_hd__xor3` | XOR | X, A, B, C | `(A&!B&!C) | (!A&B&!C) | (!A&!B&C) | (A&B&C)` | x1, x2, x4 |

## Sequential: flip-flops and latches (30)

| Interface id | Type | Ports | Behavior | Drives |
|---|---|---|---|---|
| `sky130_fd_sc_hd__dfbbn` | flip-flop | Q, Q_N, D, CLK_N, SET_B, RESET_B | Edge-triggered flip-flop; Q <= D on the falling edge of clock; async clear !RESET_B; async preset !SET_B | x1, x2 |
| `sky130_fd_sc_hd__dfbbp` | flip-flop | Q, Q_N, D, CLK, SET_B, RESET_B | Edge-triggered flip-flop; Q <= D on the rising edge of clock; async clear !RESET_B; async preset !SET_B | x1 |
| `sky130_fd_sc_hd__dfrbp` | flip-flop | Q, Q_N, CLK, D, RESET_B | Edge-triggered flip-flop; Q <= D on the rising edge of clock; async clear !RESET_B | x1, x2 |
| `sky130_fd_sc_hd__dfrtn` | flip-flop | Q, CLK_N, D, RESET_B | Edge-triggered flip-flop; Q <= D on the falling edge of clock; async clear !RESET_B | x1 |
| `sky130_fd_sc_hd__dfrtp` | flip-flop | Q, CLK, D, RESET_B | Edge-triggered flip-flop; Q <= D on the rising edge of clock; async clear !RESET_B | x1, x2, x4 |
| `sky130_fd_sc_hd__dfsbp` | flip-flop | Q, Q_N, CLK, D, SET_B | Edge-triggered flip-flop; Q <= D on the rising edge of clock; async preset !SET_B | x1, x2 |
| `sky130_fd_sc_hd__dfstp` | flip-flop | Q, CLK, D, SET_B | Edge-triggered flip-flop; Q <= D on the rising edge of clock; async preset !SET_B | x1, x2, x4 |
| `sky130_fd_sc_hd__dfxbp` | flip-flop | Q, Q_N, CLK, D | Edge-triggered flip-flop; Q <= D on the rising edge of clock | x1, x2 |
| `sky130_fd_sc_hd__dfxtp` | flip-flop | Q, CLK, D | Edge-triggered flip-flop; Q <= D on the rising edge of clock | x1, x2, x4 |
| `sky130_fd_sc_hd__dlrbn` | latch | Q, Q_N, RESET_B, D, GATE_N | Level-sensitive D latch; Q follows D while !GATE_N is asserted; async clear !RESET_B | x1, x2 |
| `sky130_fd_sc_hd__dlrbp` | latch | Q, Q_N, RESET_B, D, GATE | Level-sensitive D latch; Q follows D while GATE is asserted; async clear !RESET_B | x1, x2 |
| `sky130_fd_sc_hd__dlrtn` | latch | Q, RESET_B, D, GATE_N | Level-sensitive D latch; Q follows D while !GATE_N is asserted; async clear !RESET_B | x1, x2, x4 |
| `sky130_fd_sc_hd__dlrtp` | latch | Q, RESET_B, D, GATE | Level-sensitive D latch; Q follows D while GATE is asserted; async clear !RESET_B | x1, x2, x4 |
| `sky130_fd_sc_hd__dlxbn` | latch | Q, Q_N, D, GATE_N | Level-sensitive D latch; Q follows D while !GATE_N is asserted | x1, x2 |
| `sky130_fd_sc_hd__dlxbp` | latch | Q, Q_N, D, GATE | Level-sensitive D latch; Q follows D while GATE is asserted | x1 |
| `sky130_fd_sc_hd__dlxtn` | latch | Q, D, GATE_N | Level-sensitive D latch; Q follows D while !GATE_N is asserted | x1, x2, x4 |
| `sky130_fd_sc_hd__dlxtp` | latch | Q, D, GATE | Level-sensitive D latch; Q follows D while GATE is asserted | x1 |
| `sky130_fd_sc_hd__edfxbp` | flip-flop | Q, Q_N, CLK, D, DE | Edge-triggered flip-flop; Q <= (D&DE) | (IQ&!DE) on the rising edge of clock | x1 |
| `sky130_fd_sc_hd__edfxtp` | flip-flop | Q, CLK, D, DE | Edge-triggered flip-flop; Q <= (D&DE) | (IQ&!DE) on the rising edge of clock | x1 |
| `sky130_fd_sc_hd__sdfbbn` | flip-flop | Q, Q_N, D, SCD, SCE, CLK_N, SET_B, RESET_B | Edge-triggered flip-flop; Q <= (D&!SCE) | (SCD&SCE) on the falling edge of clock; async clear !RESET_B; async preset !SET_B | x1, x2 |
| `sky130_fd_sc_hd__sdfbbp` | flip-flop | Q, Q_N, D, SCD, SCE, CLK, SET_B, RESET_B | Edge-triggered flip-flop; Q <= (D&!SCE) | (SCD&SCE) on the rising edge of clock; async clear !RESET_B; async preset !SET_B | x1 |
| `sky130_fd_sc_hd__sdfrbp` | flip-flop | Q, Q_N, CLK, D, SCD, SCE, RESET_B | Edge-triggered flip-flop; Q <= (D&!SCE) | (SCD&SCE) on the rising edge of clock; async clear !RESET_B | x1, x2 |
| `sky130_fd_sc_hd__sdfrtn` | flip-flop | Q, CLK_N, D, SCD, SCE, RESET_B | Edge-triggered flip-flop; Q <= (D&!SCE) | (SCD&SCE) on the falling edge of clock; async clear !RESET_B | x1 |
| `sky130_fd_sc_hd__sdfrtp` | flip-flop | Q, CLK, D, SCD, SCE, RESET_B | Edge-triggered flip-flop; Q <= (D&!SCE) | (SCD&SCE) on the rising edge of clock; async clear !RESET_B | x1, x2, x4 |
| `sky130_fd_sc_hd__sdfsbp` | flip-flop | Q, Q_N, CLK, D, SCD, SCE, SET_B | Edge-triggered flip-flop; Q <= (D&!SCE) | (SCD&SCE) on the rising edge of clock; async preset !SET_B | x1, x2 |
| `sky130_fd_sc_hd__sdfstp` | flip-flop | Q, CLK, D, SCD, SCE, SET_B | Edge-triggered flip-flop; Q <= (D&!SCE) | (SCD&SCE) on the rising edge of clock; async preset !SET_B | x1, x2, x4 |
| `sky130_fd_sc_hd__sdfxbp` | flip-flop | Q, Q_N, CLK, D, SCD, SCE | Edge-triggered flip-flop; Q <= (D&!SCE) | (SCD&SCE) on the rising edge of clock | x1, x2 |
| `sky130_fd_sc_hd__sdfxtp` | flip-flop | Q, CLK, D, SCD, SCE | Edge-triggered flip-flop; Q <= (D&!SCE) | (SCD&SCE) on the rising edge of clock | x1, x2, x4 |
| `sky130_fd_sc_hd__sedfxbp` | flip-flop | Q, Q_N, CLK, D, DE, SCD, SCE | Edge-triggered flip-flop; Q <= (D&DE&!SCE) | (IQ&!DE&!SCE) | (SCD&SCE) on the rising edge of clock | x1, x2 |
| `sky130_fd_sc_hd__sedfxtp` | flip-flop | Q, CLK, D, DE, SCD, SCE | Edge-triggered flip-flop; Q <= (D&DE&!SCE) | (IQ&!DE&!SCE) | (SCD&SCE) on the rising edge of clock | x1, x2, x4 |

