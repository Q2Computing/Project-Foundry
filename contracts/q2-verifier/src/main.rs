//! ABI-export entrypoint. Only compiled with `--features export-abi`. For the
//! wasm build this file is `no_main`, so the deployable cdylib is unaffected.
#![cfg_attr(not(feature = "export-abi"), no_main)]

#[cfg(feature = "export-abi")]
fn main() {
    q2_verifier::print_abi("MIT-OR-APACHE-2.0", "pragma solidity ^0.8.23;");
}
