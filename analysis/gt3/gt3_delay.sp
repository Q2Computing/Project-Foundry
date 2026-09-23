* GT3 3nm inverter delay: rvt vs lvt, VDD=0.7V, 50% threshold (OSDI, N prefix)
.include "gt3_rvt_osdi.mod"
.include "gt3_lvt_osdi.mod"
.param VDD=0.7 CL=10f VM=0.35
Vdd vdd 0 {VDD}
Vin in 0 pulse(0 {VDD} 1n 20p 20p 2n 4n)
* rvt inverter (1 nmos pull-down, 2 pmos pull-up for rough balance)
Nrn orv in 0 0 nmos_rvt
Nrp1 orv in vdd vdd pmos_rvt
Nrp2 orv in vdd vdd pmos_rvt
Crv orv 0 {CL}
* lvt inverter, same geometry
Nln olv in 0 0 nmos_lvt
Nlp1 olv in vdd vdd pmos_lvt
Nlp2 olv in vdd vdd pmos_lvt
Clv olv 0 {CL}
.control
pre_osdi bsimcmg_gaa.osdi
tran 0.2p 4.4n
meas tran tphl_rv trig v(in) val=0.35 rise=1 targ v(orv) val=0.35 fall=1
meas tran tplh_rv trig v(in) val=0.35 fall=1 targ v(orv) val=0.35 rise=1
meas tran tphl_lv trig v(in) val=0.35 rise=1 targ v(olv) val=0.35 fall=1
meas tran tplh_lv trig v(in) val=0.35 fall=1 targ v(olv) val=0.35 rise=1
.endc
.end
