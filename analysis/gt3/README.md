# GT3 3nm calibration (node-portability check)

Re-measures the low-Vt calibration constants on an advanced node, to show that the
**method carries but the numbers do not**. The proving ground is sky130 (130nm);
this is the same measurement on **GT3**, an open-source 3nm GAAFET PDK from Azad
Naeemi's group at Georgia Tech (BSIM-CMG, GAA nanosheet, 0.7V).

## Why it needs a toolchain build

GT3's device models are BSIM-CMG (`level=72`, VERSION 111.2.1, `GEOMOD=5` nanosheet),
written for HSPICE. ngspice has no native BSIM-CMG, so we run it through **OSDI**:
compile a GAA-capable BSIM-CMG Verilog-A to a `.osdi` with **OpenVAF**, load it in
ngspice at runtime, and map GT3's HSPICE model cards onto the OSDI module.

Two non-obvious mappings (see `transform_gt3.sh`):
- the OSDI model ignores GT3's `DEVTYPE`; polarity is `TYPE` (`+1` NMOS, `-1` PMOS),
  so a pfet card without `TYPE=-1` silently behaves as an nfet;
- OSDI device instances must use the `N` prefix in ngspice (a `P` prefix errors).

The GAA support (`GEOMOD==5`) exists only in the **latest** VA-Models `vacode`, not
`vacode111`, which rejects `GEOMOD=5` as out of bounds.

## Run it

Needs `git` + `curl` on the host (to fetch OpenVAF, the BSIM-CMG Verilog-A, and GT3)
and the `q2edp` ngspice+OSDI container to compute:

```
./run-gt3.sh
```

`run-gt3.sh` fetches the dependencies into `build/` on the host, then runs
`calibrate.sh` inside the container to compile the OSDI model, transform the GT3
cards, and run the three decks (`gt3_delay.sp`, `gt3_leak.sp`, `gt3_energy.sp`).
None of the external sources (OpenVAF, VA-Models, GT3) are vendored here; they are
fetched at their own licenses.

## Result (measured, unit inverter, 0.7V, tt, 10fF) -> `gt3_calibration.json`

| constant | sky130 (1.8V) | GT3 3nm (0.7V) |
|---|---|---|
| Vt speedup KV | 0.189 | 0.170 |
| leak ratio (Vt swap) | 71x | 13.4x |
| dynamic energy / cycle | ~1000 fJ @250fF | ~5.06 fJ @10fF |
| abs leakage / inverter | ~2 to 160 pA | ~480 to 6500 pA |
| low-Vt energy upside | slight | none |

Findings: the Vt speedup is similar (the knob carries); the leakage **ratio** is
smaller at 3nm only because RVT already leaks heavily, while the **absolute**
leakage floor is ~100 to 200x higher; and at 3nm the low-Vt has no dynamic-energy
upside, so it is a pure critical-path speed tool. The constants do not carry across
nodes: each node re-anchors its own.
