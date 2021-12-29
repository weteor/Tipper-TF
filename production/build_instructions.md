# build instructions

## what do you need?

#### parts
| #   | name                         | comments                                                                                 |
| --- | ---------------------------- | ---------------------------------------------------------------------------------------- |
| 1   | main PCB                     | [gerber and SMT Assembly files](https://github.com/weteor/Tipper-TF/tree/main/production/PCB_TipperTF)     |
| 1   | display PCB                  | [gerber and SMT Assembly files](https://github.com/weteor/Tipper-TF/tree/main/production/PCB_DisplayBoard) |
| 4-8 | spacer PCB                   | [gerber and SMT Assembly files](https://github.com/weteor/Tipper-TF/tree/main/production/PCB_spacer)       |
| 1   | minew ms88sf2                | BT Module                                                                                |
| 1   | EPD - GDEW0154M09            | 1.54'' E-paper Display by GoodDisplay                                                    |
| 1   | 10pin, 0.5mm pitch FCP cable | same side contacts, 8cm recommended, 10cm works                                          |
| 1   | LiPo Battery (403040)        | 500mAh, 40x30x4mm, for your own safety, please use one with build in protection circuits |
| 1   | case top                     | [3DP files](https://github.com/weteor/Tipper-TF/tree/main/production/3DP_case)           |
| 1   | case bottom                  | [3DP files](https://github.com/weteor/Tipper-TF/tree/main/production/3DP_case)           |
| 8   | heat inserts m2              | holes are 3.2mm diameter                                                                 |
| 8   | 6mm m2 screws                | min. 4mm                                                                                 |
| 34  | Kailh Choc V1 switch         |                                                                                          |
| 32  | keycaps 1u                   | choc spaced (18x17mm)                                                                    |
| 2   | keycaps 1.5u                 | choc spaced (27x17mm)                                                                    |
| 6   | bumpons                      | 8mm diameter                                                                                         |
| 16  | o rings                      | OPTIONAL - can be used between case and pcb                                              |

#### tools
- soldering iron
- double sided tape
- programmer to load bootloader to ms88sf2. J-Link or similar for STM32.
- bootloader - I used the Adafruit bootloader (see my fork)

## prebuild
- check all assembled pcbs for any obvious errors like missing parts etc.
- check if the power button is set to off
- build the bootloader 
- build a zmk firmware
- use the solder iron to place the heat inserts into the case top

## build 
### main pcb
- solder the minew MS88SF2 modulet to the main pcb
- connect the main pcb 
- program bootloader to MS88SF2. You don't need to solder a pin header to the pcb. just connect the cable to a pin header, press it in the holes and angle slightly. This should give enough contact to be able to program the module.
- The tipper should appear in the file manager. If not try pressing the resetbutton twice in a short time, this should restart the module in bootloader mode. If nothing happens try to reboot your PC and try again.
- copy the zmk firmware to the tipper tf drive
- open an editor and test all keys by shortening the contacts (use your tweezers, bend paperclip etc.).
- unplug the pcb
- solder in the switches
- solder the battery cables to the pcb
- plug in the usb cable again and check if the battery loads.
- let the battery load for a bit and unplug the usb cable.
- connect the display to the Displaypcb and connect that to the main pcb with the FCP cable
- turn on the board and see if the display resets and shows the programmed image.
- everything fine? great that's it for this, make sure the pcb is turned off and on to preparing the display.

### display PCB
- connect the display to the display pcb.
- put double sided tape on the side without components.
- allign the display along the lines on the back of the pcb and slightly attach it to the tape. Be careful not to press too hard, you might want to change the position of the display.
- put everything in the case top. There are small pins that should fit right into the holes of the pcb. Space for the Display cable might be tight, but it should fit.
- check if the display sits in the center of the front opening (might be good to program connect the display to the main pcb and program a dark image to it to better see the display area).
- if your are satisfied, firmly attach the display to the tape.

### case
- place the display in the top case.
- _optional_: place O rings in the recesses around the heat insert
- place the main PCB on hte top case, align the screw holes and connect the FCP cable to the pcb. 
- place the battery in the hole over the minew module. the FCP cable should be coming out left of the battery. If it is too long to sit flat, try to tuck away the excess cable under the battery.
- make sure the battery cables can't be pierced by the switch legs or other components. I like to fix them in place with a bit of tape
- _optional_: place O rings in the recesses around the screw holes of the bottom case
- place the bottom half over the top case and screw them together with 2 or 3 screws
- add keycaps and make sure everything works without touching the case. There is a bit of wiggle room for the screws so if something scratches, loosen the screws a bit and try to push/pull the pcb a bit.
- insert the remaining screws
- glue the bumpuns in the recesses

Congratulations, you should have a functioning Tipper TF laying before you :).

Hope you will enjoy the board!
