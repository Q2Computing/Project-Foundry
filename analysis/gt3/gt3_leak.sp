* GT3 3nm inverter static leakage: rvt vs lvt, both input states, 0.7V (OSDI)
.include "gt3_rvt_osdi.mod"
.include "gt3_lvt_osdi.mod"
.param VDD=0.7
Vlo lo 0 0
Vhi hi 0 {VDD}
* A: rvt, input low (nmos off)
Nan oa lo 0 0 nmos_rvt
Nap1 oa lo pwa pwa pmos_rvt
Nap2 oa lo pwa pwa pmos_rvt
Vpa pwa 0 {VDD}
* B: rvt, input high (pmos off)
Nbn ob hi 0 0 nmos_rvt
Nbp1 ob hi pwb pwb pmos_rvt
Nbp2 ob hi pwb pwb pmos_rvt
Vpb pwb 0 {VDD}
* C: lvt, input low
Ncn oc lo 0 0 nmos_lvt
Ncp1 oc lo pwc pwc pmos_lvt
Ncp2 oc lo pwc pwc pmos_lvt
Vpc pwc 0 {VDD}
* D: lvt, input high
Ndn od hi 0 0 nmos_lvt
Ndp1 od hi pwd pwd pmos_lvt
Ndp2 od hi pwd pwd pmos_lvt
Vpd pwd 0 {VDD}
.control
pre_osdi bsimcmg_gaa.osdi
op
print i(Vpa) i(Vpb) i(Vpc) i(Vpd)
.endc
.end
