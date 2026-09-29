# buf_16 across the five sky130 libraries

PDK sky130A 0fe599b2afb6708d281543108caf8310912f54af, VDD 1.8 V, input slew 0.05n. Reference: sky130_fd_sc_hd__buf_16.
Record: `record(0xb9968a68f99ce2bd66c68f699c195466abb631ae5c932b3c30418bb706aaf531, 1, 16)`

## tt, load 60f

| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hd | 85.92 | 380.27 | 42.4 | 0.0217 | 27.526 | +0.0% | +0.0% | 1.0x |  |
| hdll | 103.21 | 390.6 | 44.86 | 0.0212 | 31.28 | +20.1% | +2.7% | 1.0x | never |
| ls | 85.78 | 402.86 | 47.68 | 0.0213 | 35.165 | -0.2% | +5.9% | 1.0x | never |
| ms | 77.07 | 401.61 | 48.7 | 0.0953 | 35.165 | -10.3% | +5.6% | 4.4x | never |
| hs | 64.75 | 390.39 | 45.89 | 1.6831 | 35.165 | -24.6% | +2.7% | 77.6x | never |

## tt, load 250f

| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hd | 145.73 | 1007.8 | 42.39 | 0.0217 | 27.526 | +0.0% | +0.0% | 1.0x |  |
| hdll | 175.14 | 1018.52 | 44.86 | 0.0212 | 31.28 | +20.2% | +1.1% | 1.0x | never |
| ls | 140.66 | 1032.17 | 47.67 | 0.0213 | 35.165 | -3.5% | +2.4% | 1.0x | never |
| ms | 128.07 | 1031.34 | 48.7 | 0.0953 | 35.165 | -12.1% | +2.3% | 4.4x | never |
| hs | 107.82 | 1019.28 | 45.88 | 1.6831 | 35.165 | -26.0% | +1.1% | 77.6x | never |

## tt, load 1000f

| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hd | 367.33 | 3442.46 | 42.39 | 0.0217 | 27.526 | +0.0% | +0.0% | 1.0x |  |
| hdll | 439.43 | 3453.37 | 44.85 | 0.0212 | 31.28 | +19.6% | +0.3% | 1.0x | never |
| ls | 342.15 | 3468.04 | 47.67 | 0.0213 | 35.165 | -6.9% | +0.7% | 1.0x | never |
| ms | 313.63 | 3467.93 | 48.71 | 0.0953 | 35.165 | -14.6% | +0.7% | 4.4x | never |
| hs | 265.93 | 3455.51 | 45.87 | 1.6831 | 35.165 | -27.6% | +0.4% | 77.6x | never |

## ss, load 60f

| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hd | 122.64 | 386.25 | 42.94 | 0.02 | 27.526 | +0.0% | +0.0% | 1.0x |  |
| hdll | 140.84 | 395.69 | 45.29 | 0.02 | 31.28 | +14.8% | +2.4% | 1.0x | never |
| ls | 117.85 | 409.89 | 48.76 | 0.02 | 35.165 | -3.9% | +6.1% | 1.0x | never |
| ms | 103.13 | 407.19 | 49.69 | 0.0244 | 35.165 | -15.9% | +5.4% | 1.2x | never |
| hs | 91.18 | 396.78 | 47.02 | 0.0255 | 35.165 | -25.7% | +2.7% | 1.3x | never |

## ss, load 250f

| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hd | 206.27 | 1012.93 | 42.94 | 0.02 | 27.526 | +0.0% | +0.0% | 1.0x |  |
| hdll | 235.66 | 1022.67 | 45.29 | 0.02 | 31.28 | +14.2% | +1.0% | 1.0x | never |
| ls | 192.95 | 1039.11 | 48.76 | 0.02 | 35.165 | -6.5% | +2.6% | 1.0x | never |
| ms | 170.4 | 1037.07 | 49.69 | 0.0244 | 35.165 | -17.4% | +2.4% | 1.2x | never |
| hs | 152.04 | 1025.89 | 47.03 | 0.0255 | 35.165 | -26.3% | +1.3% | 1.3x | never |

## ss, load 1000f

| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hd | 515.64 | 3446.33 | 42.94 | 0.02 | 27.526 | +0.0% | +0.0% | 1.0x |  |
| hdll | 584.28 | 3456.27 | 45.29 | 0.02 | 31.28 | +13.3% | +0.3% | 1.0x | never |
| ls | 467.43 | 3473.89 | 48.76 | 0.02 | 35.165 | -9.3% | +0.8% | 1.0x | never |
| ms | 415.14 | 3472.6 | 49.69 | 0.0244 | 35.165 | -19.5% | +0.8% | 1.2x | never |
| hs | 374.66 | 3461.22 | 47.03 | 0.0255 | 35.165 | -27.3% | +0.4% | 1.3x | never |

## ff, load 60f

| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hd | 64.9 | 375.17 | 41.78 | 0.1165 | 27.526 | +0.0% | +0.0% | 1.0x |  |
| hdll | 80.69 | 385.9 | 44.71 | 0.0553 | 31.28 | +24.3% | +2.9% | 0.5x | never |
| ls | 66.55 | 396.31 | 46.72 | 0.0938 | 35.165 | +2.5% | +5.6% | 0.8x | never |
| ms | 60.32 | 396.76 | 47.55 | 3.9034 | 35.165 | -7.1% | +5.8% | 33.5x | never |
| hs | 49.21 | 388.54 | 44.4 | 56.6945 | 35.165 | -24.2% | +3.6% | 486.6x | never |

## ff, load 250f

| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hd | 111.69 | 1002.46 | 41.79 | 0.1165 | 27.526 | +0.0% | +0.0% | 1.0x |  |
| hdll | 139.54 | 1013.59 | 44.72 | 0.0553 | 31.28 | +24.9% | +1.1% | 0.5x | never |
| ls | 110.18 | 1025.04 | 46.71 | 0.0938 | 35.165 | -1.4% | +2.3% | 0.8x | never |
| ms | 101.56 | 1024.82 | 47.55 | 3.9034 | 35.165 | -9.1% | +2.2% | 33.5x | never |
| hs | 82.68 | 1014.52 | 44.4 | 56.6945 | 35.165 | -26.0% | +1.2% | 486.6x | never |

## ff, load 1000f

| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hd | 285.41 | 3438.49 | 41.79 | 0.1165 | 27.526 | +0.0% | +0.0% | 1.0x |  |
| hdll | 355.46 | 3449.72 | 44.72 | 0.0553 | 31.28 | +24.5% | +0.3% | 0.5x | never |
| ls | 271.23 | 3461.94 | 46.7 | 0.0938 | 35.165 | -5.0% | +0.7% | 0.8x | never |
| ms | 251.89 | 3462.14 | 47.55 | 3.9034 | 35.165 | -11.7% | +0.7% | 33.5x | never |
| hs | 206.33 | 3451.43 | 44.4 | 56.6945 | 35.165 | -27.7% | +0.4% | 486.6x | never |

