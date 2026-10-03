# OCP Microscaling (MX) interface contracts

Per the **OCP Microscaling Formats (MX) Specification v1.0**. MXFP4 uses 4-bit **E2M1**
elements (1 sign / 2 exponent / 1 mantissa) grouped in blocks of **K = 32** that share one
8-bit **E8M0** power-of-two scale. Products reduce into an IEEE 754 binary32 accumulator.

| Interface id | Device | Ports | Semantics | Notes |
|---|---|---|---|---|
| `q2_if.mx_e2m1_decode` | E2M1 element decode | `val[31:0], e2m1[3:0]` | Decode one OCP MX FP4 (E2M1) element to its real value. | E2M1 = 1 sign / 2 exponent / 1 mantissa bit; value set {0, +/-0.5, +/-1, +/-1.5, +/-2, +/-3, +/-4, +/-6}. |
| `q2_if.mxfp4_lane_mul` | MXFP4 lane multiply | `p[?:0], a_e2m1[3:0], b_e2m1[3:0]` | p = decode(a) * decode(b) for one element pair. | Per-element product ahead of block reduction. Scales applied at block level, not per lane. |
| `q2_if.mxfp4_dot32` | MXFP4 block dot-product | `acc[31:0], a_blk[127:0], b_blk[127:0], a_scale[7:0], b_scale[7:0]` | acc = (a_scale*b_scale) * sum_{i=0..31} decode(a_i)*decode(b_i) | OCP MX block of K=32 E2M1 elements with one shared E8M0 (8-bit power-of-two) scale each. Accumulate to binary32. |
| `q2_if.mxfp4_pe` | MXFP4 accumulating PE | `acc_out[31:0], a_blk, b_blk, a_scale, b_scale, acc_in[31:0]` | acc_out = acc_in + mxfp4_dot32(...) | One accumulating processing element: a block dot-product added to a running binary32 accumulator. |
