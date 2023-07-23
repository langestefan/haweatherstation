### Step 1: Install rtl_433

First install `rtl_433` via apt-get:

```
sudo apt-get install rtl-433
```

### Step 2: Locate RTL-SDR USB device

Run the `lsusb` command to list all USB devices connected to your computer:

```
lsusb -vvv
```

Locate the RTL-SDR device. In my case it was the following:

```
Bus 001 Device 004: ID 0bda:2838 Realtek Semiconductor Corp. RTL2838 DVB-T
Device Descriptor:
  bLength                18
  bDescriptorType         1
  bcdUSB               2.00
  bDeviceClass            0 
  bDeviceSubClass         0 
  bDeviceProtocol         0 
  bMaxPacketSize0        64
  idVendor           0x0bda Realtek Semiconductor Corp.
  idProduct          0x2838 RTL2838 DVB-T
```

Note down `idVendor` and `idProduct` because we need them in step 3. In my case they were `0x0bda` and `0x2838` respectively.

> See also: [change-usb-device-permission-linux](https://www.xmodulo.com/change-usb-device-permission-linux.html)

### Step 3: Create udev rule

Create a new udev rule file in /etc/udev/rules.d/ directory. I named mine 50-myusb.rules. The name doesn't matter as long as it ends with .rules. 

Create the file with the following command:

```
sudo nano /etc/udev/rules.d/50-myusb.rules
```

The file should contain the following line:

```
SUBSYSTEMS=="usb", ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303", GROUP="users", MODE="0666"
```

Replace `idVendor` and `idProduct` with the values you noted down in step 2. In my case the line looked like this:

```
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", GROUP="users", MODE="0666"
```

Save the file and exit nano (Ctrl+X, Y, Enter). Reload the udev rules with the following command:

```
sudo udevadm control --reload-rules
```

### Step 4: Test rtl_433

Run the following command to test if rtl_433 is working:

```
rtl_433 -c /dev/swradio0 -f 868.3M
```

If everything is working correctly you should see something like this:

```
time      : 2023-07-22 23:55:28
model     : Bresser-5in1 id        : 176
Battery   : 1            Temperature: 14.6 C       Humidity  : 91            Wind Gust : 2.0 m/s
Wind Speed: 1.2 m/s      Direction : 180.0         Rain      : 20.0 mm       Integrity : CHECKSUM
```
