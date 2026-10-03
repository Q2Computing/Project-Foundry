# IEEE 754 binary32 (FP32) device interface contracts

Operands and results are **IEEE 754-2019 binary32** fields unless stated. `rmode` selects the
rounding attribute (default roundTiesToEven). Operations marked *mandated* are defined, and where
noted correctly rounded, by IEEE 754-2019; *approximation* units operate on binary32 but are not
754-mandated and must publish their accuracy bound as part of the contract.

| Interface id | Device | Ports | Semantics | Status | Notes |
|---|---|---|---|---|---|
| `q2_if.fp32_mul` | FP32 multiplier | `p[31:0], a[31:0], b[31:0], rmode[2:0]` | p = round(a * b) | 754-mandated | Correctly-rounded binary32 product. Handle signed zero, inf, NaN, subnormals per 754-2019. |
| `q2_if.fp32_add` | FP32 adder / accumulator | `s[31:0], a[31:0], b[31:0], rmode[2:0]` | s = round(a + b) | 754-mandated | Correctly-rounded binary32 sum. Accumulator variant chains s_next = round(acc + x). |
| `q2_if.fp32_sub` | FP32 subtract | `d[31:0], a[31:0], b[31:0], rmode[2:0]` | d = round(a - b) | 754-mandated | Correctly-rounded binary32 difference. |
| `q2_if.fp32_sqrt` | FP32 square root | `q[31:0], a[31:0], rmode[2:0]` | q = round(sqrt(a)) | 754-mandated | 754-2019 mandates a correctly-rounded square root. |
| `q2_if.fp32_rne` | Round to nearest even | `y[31:0], a_wide, sticky` | y = roundTiesToEven(a_wide) | 754-mandated | The 754-2019 default rounding attribute applied to a wider intermediate. |
| `q2_if.fp32_f2i` | FP32 to Int32 convert | `i[31:0], a[31:0], rmode[2:0]` | i = convertToInteger(a) | 754-mandated | 754-2019 convertToInteger; signal/saturate on overflow and NaN per the chosen policy (state it). |
| `q2_if.fp32_i2f` | Int32 to FP32 convert | `y[31:0], i[31:0], rmode[2:0]` | y = round(real(i)) | 754-mandated | 754-2019 convertFromInt; round when |i| exceeds 24-bit exact range. |
| `q2_if.fp32_maxmin` | FP32 max / min | `y[31:0], a[31:0], b[31:0], sel` | y = sel ? maxNum(a,b) : minNum(a,b) | 754-mandated | 754-2019 maximumNumber / minimumNumber NaN-handling. |
| `q2_if.fp32_relu` | FP32 ReLU | `y[31:0], a[31:0]` | y = (a > +0) ? a : +0 | exact (non-754) | Exact on binary32; not a 754-defined op. Define NaN pass-through. |
| `q2_if.fp32_normpack` | FP32 normalize / pack | `y[31:0], sign, exp_wide, mant_wide` | y = pack_round(sign, exp, mant) | exact (non-754) | Exact: normalize an unpacked (sign, exponent, significand) triple to a rounded binary32 field. Building block. |
| `q2_if.fp32_recip` | FP32 reciprocal (SFU) | `y[31:0], a[31:0]` | y ~= 1/a | approximation | binary32 approximation (e.g. Newton-Raphson). Publish the achieved ULP/relative-error bound as part of the contract. |
| `q2_if.fp32_rsqrt` | FP32 reciprocal sqrt (SFU) | `y[31:0], a[31:0]` | y ~= 1/sqrt(a) | approximation | binary32 approximation. Publish the achieved accuracy bound. |
| `q2_if.fp32_exp2` | FP32 base-2 exponential (SFU) | `y[31:0], a[31:0]` | y ~= 2**a | approximation | binary32 approximation. Publish the achieved accuracy bound. |
