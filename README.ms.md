# Project Foundry: ekonomi bukti

Baca dalam: [English](README.md) · Bahasa Melayu · [简体中文](README.zh.md) · [தமிழ்](README.ta.md)

Bukti bagi sesuatu litar ialah sijil. Sijil dilesenkan ke dalam bukti yang lebih besar dan ke dalam silikon yang dikilangkan, dengan harga lantai yang tidak dapat ditandingi oleh mana-mana pesaing, dan diselesaikan di Arbitrum Stylus. Pengesahan dikongsi, bukan diulang: sesuatu blok dibuktikan sekali, secara terbuka, dan setiap sistem yang dibina di atasnya mewarisi bukti itu.

Repositori ini ialah contoh awam ekonomi tersebut. Ia mengandungi gelung yang mengatasi sel kilang (foundry) dan membuktikannya, kontrak yang menyelesaikan bukti di atas rantaian, dan tahap bukti yang menggredkan setiap sijil. Rekod saintifik di sebalik setiap angka terdapat dalam [RESEARCH.md](RESEARCH.md) (dalam bahasa Inggeris).

## Tahap bukti

Setiap sijil menamakan tahap di mana bloknya dibuktikan. Tangga ini bermula daripada bukti terhad yang terkuat hingga bukti yang berskala tanpa had. Di atas tangga terletak bukti yang memberinya makna dan kepercayaan.

| Tahap | Apa yang dibuktikan | Cara | Jangkauan | Status di sini |
| --- | --- | --- | --- | --- |
| 1. Menyeluruh (exhaustive) | Blok mengira keluaran yang betul bagi setiap input | Senaraikan seluruh ruang input (jadual kebenaran sel dalam SPICE daripada transistor PDK; penambah 8-bit merentasi kesemua 131,072 input) | Blok kecil sahaja; kos meningkat sebanyak 2 kuasa lebar input | Terbukti: bukti sel SPICE, adder8 |
| 2. Kesetaraan (equivalence) | Dua perwakilan mengira fungsi yang sama | Miter SAT antara netlist dan RTL, aruhan temporal bagi logik berjujukan; simbolik, jadi tiada penyenaraian | Mana-mana blok yang dapat diselesaikan oleh penyelesai | Terbukti: Yosys SAT |
| 3. Pemetaan teknologi (techmap) ke sel terbukti | Netlist hanya menggunakan sel yang dibuktikan pada tahap 1 dan setara secara struktur dengan RTLnya | Petakan ke pustaka terbukti, kemudian semakan kesetaraan struktur | Mana-mana blok, dihadkan oleh had primitif 64 sel bagi setiap daun | Terbukti |
| 4. Komposisi | Blok yang lebih besar adalah betul kerana ia dibina hanya daripada bahagian terbukti dan perekat terbukti, terikat kepada anak yang diisytiharkan | Bancian bahagian serta kesetaraan pemasangan dengan komposisi; had itu memaksa apa-apa yang lebih besar untuk diuraikan | Tanpa had: komposit ialah bahagian bagi tahap seterusnya | Terbukti: anak tangga yang berskala |

Komposisi ialah puncak tangga ketepatan dan ia tertutup: blok yang dikomposisikan ialah bahagian bagi komposisi seterusnya, jadi tangga ini berskala tanpa had. Tiga bukti terletak di atas atau di sebelahnya.

| Di atas tangga | Apa yang ditambah | Status di sini |
| --- | --- | --- |
| Penghalusan kepada spesifikasi | Sistem yang dikomposisikan memenuhi piawaian yang didakwanya (pembundaran betul IEEE 754, ISA RISC-V), bukan sekadar sama dengan RTLnya sendiri. Ini memberi makna kepada antara muka peringkat atas. | Pelan hala tuju: anak tangga seterusnya untuk dibina |
| Kesahihan peraturan komposisi | Teorem yang disemak mesin bahawa bahagian terbukti serta perekat terbukti menghasilkan keseluruhan yang terbukti, mewajarkan tahap 4 bagi setiap contoh sekaligus | Pelan hala tuju |
| Kepercayaan pembawa bukti dan pengesahan (attestation) | Sijil bukti yang dimainkan semula oleh penyemak yang disahkan, supaya tiada penyelesai dipercayai atas kata-katanya; dan rantaian jagaan daripada reka bentuk terbukti ke silikon yang dikilangkan | Separa: jagaan beralamat kandungan adalah sebenar; main semula sijil dan pengesahan silikon ialah pelan hala tuju |

Simulasi dengan vektor ujian ialah keterangan, bukan bukti. Ia direkodkan, dan ia tidak pernah memajukan sijil dengan sendirinya.

## Ekonomi

Dua lesen berada pada setiap sijil. Protokol mengambil sifar dalam kedua-duanya.

**Rujukan: milik bersama (commons).** Primitif PDK kilang bebas untuk dirujuk selama-lamanya. Setiap sijil lain hanya memulihkan gas penyenaraiannya, dibayar oleh abstraksi yang menggunakannya secara langsung, dihadkan pada gas itu, kemudian ia bebas. Sesiapa yang mengatasi sesuatu blok membayar kos penyenaraiannya. Pemulihan kos, bukan sewa.

**Pembuatan: produk pereka.** Hak untuk meletakkan reka bentuk ke dalam SoC yang difabrikasi. Reka bentuk hanya diserahkan kepada kilang yang dinamakan oleh pereka, yang mesti membuktikan ia telah menerima pakej yang dikomitkan sebelum ia boleh menggunakan satu unit pun. Pemegang lesen tidak pernah memuat turun fail itu. Harganya ialah harga lantai: $100 bagi setiap set topeng (mask set), meliputi setiap blok yang disijilkan dalam topeng itu, diturunkan seiring dengan peningkatan penerimaan sehingga ia menumpu kepada kos fizikal sebenar untuk menghasilkan dan menyelesaikan sesuatu bukti.

## Kontrak

Tiga kontrak Arbitrum Stylus, satu bagi setiap mod penyelesaian.

| Kontrak | Mod | Apa yang dilakukan oleh rantaian |
| --- | --- | --- |
| q2-verifier | Sahkan semula | Menjalankan semula bukti terhad di atas rantaian. Tanpa perlu kepercayaan. |
| q2-anchor | Sauh | Merekodkan komitmen beralamat kandungan bagi bukti luar rantaian dengan label penambahbaikan. |
| q2-composition | Komposisi dan lesen | Mensijilkan sistem yang lebih besar melalui rujukan kepada sijil anak dan menyelesaikan kedua-dua lesen. |

## Gelung yang menyuapnya

Pilih sel piawai yang dibekalkan oleh kilang. Biarkan ejen mereka bentuk sel tersuai yang mengatasinya dari segi keluasan, kelajuan dan tenaga. Ukur semula segala-galanya secara terbuka, dari awal, dalam integrasi berterusan. Sauhkan kemenangan itu di atas rantaian tanpa menerbitkan reka bentuk.

```
  jana                     nilai (oracle)                    sauh
  ejen mencadangkan  ==>   CI mengukur semula garis    ==>   hash + label
  sel calon                asas dan setiap calon dalam        direkodkan di atas
                           satu bangku ngspice pada PDK       rantaian; netlist
                           sky130 terbuka                     kekal peribadi
```

Dua sifat menjadikannya boleh dipercayai. Penilai bebas daripada penjana: penjanaan boleh menggunakan mana-mana model secara luar talian, penilaian bersifat penentu dan berjalan dalam CI, jadi keputusannya ialah artifak awam yang boleh dijalankan semula oleh sesiapa sahaja. Dan semua diukur dengan pembaris yang sama: satu bangku ujian ngspice, beban, slew dan sudut yang sama, peranti PDK yang sama, bagi sel tersuai dan sel kilang.

## Apa yang sebenar dan apa yang pelan hala tuju

Terbukti: tahap 1 hingga 4 tangga, tiga kontrak, demo yang menjalankan pemecut GEMM MXFP4 sebenar melalui kedua-dua lesen, dan pakej bukti Lean bagi ekonomi tersebut. Pelan hala tuju: penghalusan kepada spesifikasi, teorem kesahihan bagi komposisi, main semula sijil, dan pengesahan silikon. Garis antara kedua-duanya dikekalkan jujur dalam [RESEARCH.md](RESEARCH.md).
