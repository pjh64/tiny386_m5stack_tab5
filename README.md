# Tiny386 for the M5stack Tab5
An optimized x86 PC emulator in C99, modified from [hchunhui/tiny386](https://github.io) to run classic operating systems like Windows 9x and Linux on the M5stack Tab5.

## Introduction
This is my attempt on porting tiny386, a x86 emulator for esp32 to the M5stack Tab5. This is very much WIP and not fully functional yet.

It already boots several vintage OS images such as win9x, historical Linux or KolibriOS.
It supports graphical output stretched over the Tab5's 1280×720 display, and can be used with USB mice and keyboards.


<img width="3840" height="2160" alt="image20260901_125256982" src="https://github.com/user-attachments/assets/9e7f8d89-c494-4590-a58e-a2a73a995765" />
(Don't expect it to ever run ZSNES on acceptable framerates, but it can start ZSNES in a Win9x/DOS-Environment)
<img width="3840" height="2160" alt="image20260903_231915111" src="https://github.com/user-attachments/assets/ce121685-cd63-4785-89e3-37a4b8ed339b" />
(This takes some time to boot, WIP) 

## License
The cpu emulator and the project as a whole are both licensed under the BSD-3-Clause license.

Adlib emulation is an optional part of the project, and it requires the library fmopl which is licensed under the LGPL.
Use `make USE_FMOPL=n` to build without adlib emulation.

SeaBIOS is distributed under the GNU LGPL-3 license.

Some parts ported from QEMU/TinyEMU are under the MIT license.
