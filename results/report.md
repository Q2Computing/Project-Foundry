# EDP assessment: custom drivers vs `buf_16`

Part to beat: **sky130_fd_sc_hd__buf_16** at load **250f**, slew 0.05n, corner tt.
Every row measured in the same ngspice bench against the open sky130
PDK. Primary figure of merit: **EDP = energy x delay** ('do more with less'). Area is the reported cost of extra speed, never hidden.

| design | tpd (ns) | E (fJ) | area (um) | EDP | dEDP | verdict |
|---|---|---|---|---|---|---|
| **buf_16** | 0.1457 | 1007.8 | 36.3 | 146.86 | n/a | part to beat |
| drive32_2stage_f2p5 | 0.1043 | 1199.4 | 74.2 | 125.10 | +14.8% | **beats part (EDP)** |
| drive32_2stage_f3 | 0.1109 | 1191.0 | 70.9 | 132.13 | +10.0% | **beats part (EDP)** |
| drive40_2stage_f3 | 0.1053 | 1278.6 | 87.5 | 134.64 | +8.3% | **beats part (EDP)** |
| drive48_2stage_f3 | 0.0986 | 1368.0 | 105.6 | 134.95 | +8.1% | **beats part (EDP)** |
| drive24_2stage_f3 | 0.1254 | 1098.7 | 52.8 | 137.78 | +6.2% | **beats part (EDP)** |
| buf16_equivalent_validator | 0.1457 | 1007.8 | 36.3 | 146.86 | +0.0% | part wins |
| underdrive10_loses | 0.1878 | 935.9 | 23.1 | 175.75 | -19.7% | part wins |
| drive32_4stage_f3 | 0.2351 | 1306.8 | 79.2 | 307.27 | -109.2% | part wins |

## Verdict

5 unique functional candidate(s) beat the foundry part on EDP.

Best: `drive32_2stage_f2p5` at **+14.8% EDP** and **+28% speed** vs `sky130_fd_sc_hd__buf_16` (tpd 0.1043 ns, E 1199.4 fJ, area 74.2 um vs the part's 36.3 um). The ladder caps at its top drive strength; this load wants more, so the custom cell extends the frontier past the cap. It does **not** Pareto-dominate; the extra speed costs area and energy, which is the honest shape of beating a frontier point.

_Deck-clean + SPICE-characterized on the open PDK, not foundry-qualified. `area_um` is a transistor-width proxy, not laid-out area._
