# pymt500 on Raspberry Pi 3

Edit `/boot/config.txt` with the contents of `config.txt` in this directory. This will disable bluetooth but allow you to use the hardware serial port (/dev/ttyAMA0). Important lines to note are `enable_uart=1` and `dtoverlay=pi3-disable-bt`.

For more information: https://spellfoundry.com/2016/05/29/configuring-gpio-serial-port-raspbian-jessie-including-pi-3/ 

Pin 8  - TX (GPIO14)
Pin 10 - RX (GPIO15)

For pinout run:
```
pinout
```
