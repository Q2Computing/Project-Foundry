# Local driver for the EDP system (Windows). Runs the same ngspice measurement
# the CI oracle runs, in a container, against the local sky130 PDK.
#
#   ./run.ps1 assess     # re-measure committed candidates vs the part (gate)
#   ./run.ps1 propose    # search the design grid, write survivors to manifest
#   ./run.ps1 anchor     # prepare disclosure-safe provenance records
#
# Override the PDK with:  $env:PDK="C:\path\to\sky130A"; ./run.ps1 assess
param([string]$Cmd = "assess")
$ErrorActionPreference = "Stop"
$Def = "$env:USERPROFILE\.ciel\ciel\sky130\versions\0fe599b2afb6708d281543108caf8310912f54af\sky130A"
$Pdk = if ($env:PDK) { $env:PDK } else { $Def }
if (-not (Test-Path "$Pdk\libs.tech\ngspice\sky130.lib.spice")) {
  Write-Error "sky130A not found at PDK=$Pdk (set `$env:PDK)"; exit 1
}
docker build -q -t q2edp . | Out-Null
$rest = $args
function Run { docker run --rm -v "${Pdk}:/pdk:ro" -v "${PWD}:/work" -w /work q2edp @args }
switch ($Cmd) {
  "assess"  { Run python3 tools/assess.py --gate @rest }
  "propose" { Run python3 tools/propose.py --measure @rest }
  "anchor"  { Run python3 tools/anchor.py @rest }
  default   { Write-Host "usage: run.ps1 {assess|propose|anchor} [args]"; exit 2 }
}
