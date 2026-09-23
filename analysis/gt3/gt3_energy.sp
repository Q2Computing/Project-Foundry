* GT3 3nm dynamic energy per cycle: rvt vs lvt, 0.7V, 10fF, one rise+one fall (OSDI)
.include "gt3_rvt_osdi.mod"
.include "gt3_lvt_osdi.mod"
.param VDD=0.7 CL=10f
Vin in 0 pulse(0 {VDD} 1n 20p 20p 2n 4n)
* rvt inverter on its own supply
Nrn orv in 0 0 nmos_rvt
Nrp1 orv in pr pr pmos_rvt
Nrp2 orv in pr pr pmos_rvt
Vpr pr 0 {VDD}
Crv orv 0 {CL}
* lvt inverter on its own supply
Nln olv in 0 0 nmos_lvt
Nlp1 olv in pl pl pmos_lvt
Nlp2 olv in pl pl pmos_lvt
Vpl pl 0 {VDD}
Clv olv 0 {CL}
.control
pre_osdi bsimcmg_gaa.osdi
tran 0.2p 4.4n
meas tran q_rv integ i(Vpr) from=1n to=4.9n
meas tran q_lv integ i(Vpl) from=1n to=4.9n
.endc
.end
