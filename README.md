# axi_python_utilities
Simple library to make Python driver development for AXI interfaces on Zynq platforms as simple and user friendly as possible.

## Description
Provides a base class RegisterInterface to interface to PL peripherals from userspace.

Assumes that PL peripherals addressed are using UIO drivers. Upon creation of a RegisterInterface the /sys/class/uio folder will be scraped by UIOProber and information about all UIO devices will be saved.
Subsequently, the RegisterInterface will open and mmap the file in /dev corresponding to the desired device.

In case multiple IPs with the same name are present a list will be returned and an index will have to be passed to the RegisterInterface initialization to specify which UIO device must be opened

## Usage
Import the module and make your object inherit from RegisterInterface. Examples of how to write your own module to interface to PL can be seen in sample_driver.py

### Currently unsupported features
* IPs that map multiple memory regions.
* Bitfields inside registers.

Created by Luca Della Vedova - lucadellavr@gmail.com
