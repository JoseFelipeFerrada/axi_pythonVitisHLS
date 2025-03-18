'''
Module with a bunch of utilities to map memory, access registers and to bitwise operations on them
'''

import os
import mmap
import struct
from collections import namedtuple
import json
from typing import NamedTuple

from .uio_utilities import UIOProber, UIODevice

# Type for control field. 
class RegisterField(NamedTuple):
    register_offset: int
    msb_offset: int
    length: int
    readp: bool
    writep: bool
    def __str__(self):
        str_out = f"Reg: {hex(self.register_offset):<10}"

        str_out += " access: "
        if self.readp:
            str_out += "r"
        if self.writep:
            str_out += "w"
        if self.msb_offset!=31:
            str_out += f" msb: {self.msb_offset}"
        if self.length!=32:
            str_out += f" len: {self.length}"

        return str_out

'''
Utility class to interface with AXI4 lite peripherals and perform operations on them
'''
class RegisterInterface(object):

    def __init__(self, device_name, uio_index = 0, axi_bus_width=4):
        # This struct contains all the fields we want to address
        self.fields_dict = {}
        self.bus_width = axi_bus_width
        # This class will scan all the UIO devices
        prober = UIOProber()
        try:
            device = prober.devices[device_name][uio_index]
            memory_file = os.open("/dev/" + device.uio_num, os.O_RDWR | os.O_SYNC)
            self.reg_mem = mmap.mmap(memory_file, device.map_length, prot=mmap.PROT_READ | mmap.PROT_WRITE)
        except KeyError as e:
            # Give a more helpful error message
            e.message = ('Device with name ' + device_name + ' not found')
            raise e
        def __str__(self):
            # Find the maximum length of the field names to align them nicely
            max_field_name_length = max(len(name) for name in self.fields_dict.keys())
            
            string_out = "RegisterInterface: " + self.device_name + "\n"
            for name in self.fields_dict.keys():
                # Align field names based on the maximum field name length
                string_out += f"{name:<{max_field_name_length}} : {str(self.fields_dict[name])}\n"
            
            return string_out

    # This function adds a new register field to the list
    def AddField(self, register_name, register_offset,readp=True,writep=True ,msb_offset = None, length = None):
        # Evaluate parameters to default
        if msb_offset is None:
            msb_offset = self.bus_width * 8 - 1
        if length is None:
            length = self.bus_width * 8
        if register_offset < 0 or msb_offset < 0 or length < 0:
            raise ValueError('Parameters must be greater than 0')
        elif length - 1 > msb_offset:
            raise ValueError('Specified length is larger than available bits in register')
        elif msb_offset > 8 * self.bus_width - 1:
            raise ValueError('Offset is larger than AXI4 bus width')
        elif register_offset % self.bus_width != 0:
            raise ValueError('Register offset is not multiple of AXI4 bus width')
        elif register_name in self.fields_dict:
            raise ValueError('Register with specified name already exists')
        # We don't want this case until we actually implement it
        elif msb_offset != 31 or length != 32:
            raise NotImplementedError('Addressing inside a 32 bit register is not implemented yet')
        self.fields_dict[register_name] = RegisterField(register_offset, msb_offset, length,readp,writep)

    # Utility functions to set and clear bits, arguably we barely need to set so many bits and we need the single bit functions more
    def SetBits(self, value, offset, length):
        mask = 2 ** length - 1
        return value | (mask << (offset - length + 1))

    def ClearBits(self, value, offset, length):
        mask = 2 ** length - 1
        return value & ~(mask << (offset - length + 1))

    # UNIMPLEMENTED
    def WriteBits(self):
        pass

    def ReadBits(self):
        pass

    # Utility to write a certain value to a register field.
    # TODO FOR BOTH FUNCTIONS, make them work with registers shorter then a whole register, now they don't set single bits
    def WriteRegister(self, field_name, value):
        if field_name not in self.fields_dict:
            raise ValueError('Specified register not added to list')
        if value < 0 or value > 2 ** (self.fields_dict[field_name].length) - 1:
            raise ValueError('Value out of bounds')
        # Now write to the actual address
        self.reg_mem.seek(self.fields_dict[field_name].register_offset)
        self.reg_mem.write(struct.pack('i',value))

    # And read to register field
    def ReadRegister(self, field_name):
        if field_name not in self.fields_dict:
            raise ValueError('Specified register not added to list')
        self.reg_mem.seek(self.fields_dict[field_name].register_offset)
        return struct.unpack('i', self.reg_mem.read(self.bus_width))[0]
    

class HLSDrivers(RegisterInterface):
    def __init__(self,header_file,uioDevice):
        self.header_file = header_file
        self.uioDevice = uioDevice
        self.fields_dict = {}
        self.bus_width = 4
        self.reg_mem = "self.uioDevice.reg_mem"
        self.parseJSON()

    def __str__(self):
        # Find the maximum length of the field names to align them nicely
        max_field_name_length = max(len(name) for name in self.fields_dict.keys())
        
        # Initialize the string output
        string_out = f"HLSDriver:links {str(self.uioDevice)} with {self.header_file}\n"
        
        # Loop through each field and align the names and values
        for name in self.fields_dict.keys():
            # Use the max_field_name_length to ensure all field names are aligned
            string_out += f"\t{name:<{max_field_name_length}} : {str(self.fields_dict[name])}\n"
        
        return string_out
    def parseJSON(self):
        with open(self.header_file) as f:
            data = json.load(f)
            print(data)
            for name in data.keys():
                readpl="Read" in data[name]["access"]
                writepl="Write" in data[name]["access"]
                self.AddField(name,data[name]["address"],readp=readpl,writep=writepl)
        return data


