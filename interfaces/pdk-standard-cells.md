# sky130 PDK standard-cell interface contracts

Generic SkyWater **sky130_fd_sc_hd** standard cells. Function and ports are extracted
directly from the open-source PDK Liberty/blackbox; every cell also carries the four
standard power/bulk pins `VPWR, VGND, VPB, VNB`. These are public PDK facts, not Q2 designs.

Compete on area / delay / energy at a fixed drive strength; the interface is the Boolean
function and pin list. Drive strengths shown are those instantiated in the reference build.

| Interface id | Cell | Ports | Function | Drives |
|---|---|---|---|---|
| `sky130_fd_sc_hd__inv` | Inverter | Y, A | `Y = !A` | x1, x2, x4, x6, x8, x12, x16 |
| `sky130_fd_sc_hd__buf` | Buffer | X, A | `X = A` | x1, x2, x4, x6, x8, x12, x16 |
| `sky130_fd_sc_hd__nand2` | 2-input NAND | Y, A, B | `Y = !(A & B)` | x1, x2, x4, x8 |
| `sky130_fd_sc_hd__nand3` | 3-input NAND | Y, A, B, C | `Y = !(A & B & C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__nor2` | 2-input NOR | Y, A, B | `Y = !(A | B)` | x2, x4, x8 |
| `sky130_fd_sc_hd__nor3` | 3-input NOR | Y, A, B, C | `Y = !(A | B | C)` | x1, x2, x4 |
| `sky130_fd_sc_hd__and2` | 2-input AND | X, A, B | `X = A & B` | x1, x2, x4 |
| `sky130_fd_sc_hd__and3` | 3-input AND | X, A, B, C | `X = A & B & C` | x1, x2, x4 |
| `sky130_fd_sc_hd__or2` | 2-input OR | X, A, B | `X = A | B` | x1, x2, x4 |
| `sky130_fd_sc_hd__or3` | 3-input OR | X, A, B, C | `X = A | B | C` | x1, x2, x4 |
| `sky130_fd_sc_hd__xor2` | 2-input XOR | X, A, B | `X = A ^ B` | x1, x2, x4 |
| `sky130_fd_sc_hd__xor3` | 3-input XOR | X, A, B, C | `X = A ^ B ^ C` | x1 |
| `sky130_fd_sc_hd__xnor2` | 2-input XNOR | Y, A, B | `Y = !(A ^ B)` | x1, x2, x4 |
| `sky130_fd_sc_hd__mux2` | 2:1 multiplexer | X, A0, A1, S | `X = S ? A1 : A0` | x1, x2, x4, x8 |
| `sky130_fd_sc_hd__maj3` | 3-input majority | X, A, B, C | `X = (A&B) | (A&C) | (B&C)` | x1 |
| `sky130_fd_sc_hd__a21o` | AND2-OR (2-1) | X, A1, A2, B1 | `X = (A1 & A2) | B1` | x1, x2, x4 |
| `sky130_fd_sc_hd__a21oi` | AND2-OR-INVERT (2-1) | Y, A1, A2, B1 | `Y = !((A1 & A2) | B1)` | x1 |
| `sky130_fd_sc_hd__a22o` | AND2-OR (2-2) | X, A1, A2, B1, B2 | `X = (A1 & A2) | (B1 & B2)` | x1 |
| `sky130_fd_sc_hd__a22oi` | AND2-OR-INVERT (2-2) | Y, A1, A2, B1, B2 | `Y = !((A1 & A2) | (B1 & B2))` | x1 |
| `sky130_fd_sc_hd__o21a` | OR2-AND (2-1) | X, A1, A2, B1 | `X = (A1 | A2) & B1` | x1, x2, x4 |
| `sky130_fd_sc_hd__o21ai` | OR2-AND-INVERT (2-1) | Y, A1, A2, B1 | `Y = !((A1 | A2) & B1)` | x1 |
| `sky130_fd_sc_hd__o22a` | OR2-AND (2-2) | X, A1, A2, B1, B2 | `X = (A1 | A2) & (B1 | B2)` | x1 |
| `sky130_fd_sc_hd__o22ai` | OR2-AND-INVERT (2-2) | Y, A1, A2, B1, B2 | `Y = !((A1 | A2) & (B1 | B2))` | x1 |
| `sky130_fd_sc_hd__dfxtp` | Positive-edge D flip-flop | Q, CLK, D | `Q <= D at the rising edge of CLK` | x1 |

Reference drive-1 signatures (`Y = !A`, `Y = !(A & B)`, edge-triggered Q) are the first three posted on the witness board.
