# Tipper-TF
34 keys split unibody BLE keyboard. 
![top](https://raw.githubusercontent.com/weteor/Tipper-TF/main/img/TipperRev2_top.jpg)

- low profile
- choc v1
- 1.54'' epaper display
- angled hands
- splayed columns
- variable height on outer colum. Can be adjusted by a combination of pinheaders(1.27mm pitch, 1mm or 1.5mm height) + (at the moment) spacer pcbs.
- BLE w/ ZMK
- case files are supplied (cadquery for rev1, freecad for rev2)

## rev 2

![front](https://raw.githubusercontent.com/weteor/Tipper-TF/main/img/TipperRev2_front.jpg)
![back](https://raw.githubusercontent.com/weteor/Tipper-TF/main/img/TipperRev2_back.jpg)

Prototypes for rev 2 are there. Main PCB and case are ok. Displayboard needs some work.

**I am not sure if everything works out as intended. If you can, please wait till I verified the prototype works before building one yourself**

### changes rev 2
- encoder is gone, too high and it's hard to find a knob with the right dimensions (well, and i don't use it to be honest).
- instead an 1.54'' epaper display (good display GDEW0154M09 recommended because of the very fast refresh (0.83s full refresh)
- new case design. 
  - lower angle, but same space for the thumbs. 
  - 2-3mm lower, because the battery can move up to the space the encoder occupied before.
  - less bulk overall
- SMT Assembly files for main PCB and Display daughter board

## all files are considered untested prototypes, please don't use them to make your own board just yet. 
rev 1 works fine, but the pcb doesn't exactly match the case. But with a little bit of cutting that can easily be fixed.
rev 1 case is good, but the angle is a bit too high, so with MBK keycaps you might touch the case sometimes.

### firmware 
ZMK, config can be found [here](https://github.com/weteor/Tipper_TF-Config)

### thanks for help and inspiration:
- [MangoIV](https://github.com/MangoIV/) and his [le-chiffre-ble](https://github.com/MangoIV/le_chiff_ble)
- [broom's](https://github.com/davidphilipbarr) [hypergolic](https://github.com/davidphilipbarr/hypergolic)
- [marv](https://github.com/MarvFPV) invaluable feedback and help with the case design
