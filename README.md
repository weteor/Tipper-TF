# Tipper-TF
34 keys split unibody BLE keyboard. 

![top](https://raw.githubusercontent.com/weteor/Tipper-TF/main/img/TipperRev2_top_.jpg)

## Features

- low profile
- choc v1 w/ choc spacing
- angled hands
- splayed columns
- variable height on outer colum. Can be adjusted by a combination of pinheaders(1.27mm pitch, 1mm or 1.5mm height) + (at the moment) spacer pcbs.
- 1.54'' epaper display
- Bluetooth and USB connection 
- case files are supplied (stl, as well as freecad files)
- ZMK firmware support

## Want one?
All production files you need to build your own Tipper TF can be found [here](https://github.com/weteor/Tipper-TF/tree/main/production).

Please see the [build instruction](https://github.com/weteor/Tipper-TF/tree/main/production/build_instructions.md) for a more detailed listing of all things needed.

All PCBs come with SMT assembly files, so you can order them fully assembled. No need to solder another 50 diodes.

The files for the case are also provided. If you don't own a 3d printer, I've used JLCPCBs printing service (MJF nylon) and it turned out very good, so maybe take a look at that option.

### firmware 
The Tipper TF uses ZMK firmware.

The zmk driver for the display driver chip is not in the official repository yet, so you will have to use [my ZMK fork](https://github.com/weteor/zmk/tree/Tipper_TF_rev2) if you want to build a firmware locally.

If you prefer the github workflow, you can find the zmk config for the Tipper TF [here](https://github.com/weteor/Tipper_TF-Config). The config is already configured to pull ZMK from my fork, so you don't have to do anything further.

### some more pictures
![front](https://raw.githubusercontent.com/weteor/Tipper-TF/main/img/TipperRev2_front.jpg)
![back](https://raw.githubusercontent.com/weteor/Tipper-TF/main/img/TipperRev2_back.jpg)

## remarks
MKB keycaps work great on the Tipper, but I very much prefer the Chicago Steno caps by Pseudoku. He provides some nice SCAD files for those, you may find them in [his github](https://github.com/pseudoku/PseudoMakeMeKeyCapProfiles). He also sells them in his shop [www.asymplex.xyz](https://www.asymplex.xyz/).

### thanks for help and inspiration:
- [MangoIV](https://github.com/MangoIV/) and his [le-chiffre-ble](https://github.com/MangoIV/le_chiff_ble)
- [broom's](https://github.com/davidphilipbarr) [hypergolic](https://github.com/davidphilipbarr/hypergolic)
- [marv](https://github.com/MarvFPV) invaluable feedback and help with the case design
