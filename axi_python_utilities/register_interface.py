'''
Module with a bunch of utilities to map memory, access registers and to bitwise operations on them
'''

import os
import mmap
import struct
from collections import namedtuple

from uio_utilities import UIOProber, UIODevice

# Type for control field. 
RegisterField = namedtuple('RegisterField', ['register_offset', 'msb_offset', 'length'])

'''
Utility class to interface with AXI4 lite peripherals and perform operations on them
'''
class RegisterInterface(object):

    def __init__(self, device_name, axi_bus_width=4):
        # This struct contains all the fields we want to address
        self.fields_dict = {}
        self.bus_width = axi_bus_width
        # This class will scan all the UIO devices
        prober = UIOProber()
        try:
            device = prober.devices[device_name]
            memory_file = os.open("/dev/" + device.uio_num, os.O_RDWR | os.O_SYNC)
            self.reg_mem = mmap.mmap(memory_file, device.map_length, prot=mmap.PROT_READ | mmap.PROT_WRITE)
        except KeyError as e:
            # Give a more helpful error message
            e.message = ('Device with name ' + device_name + ' not found')
            raise e

    # This function adds a new register field to the list
    def AddField(self, register_name, register_offset, msb_offset = None, length = None):
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
        self.fields_dict[register_name] = RegisterField(register_offset, msb_offset, length)

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
        if not field_name in self.fields_dict:
            raise ValueError('Specified register not added to list')
        if value < 0 or value > 2 ** (self.fields_dict[field_name].length) - 1:
            raise ValueError('Value out of bounds')
        # Now write to the actual address
        self.reg_mem.seek(self.fields_dict[field_name].register_offset)
        self.reg_mem.write(struct.pack('i',value))

    # And read to register field
    def ReadRegister(self, field_name):
        if not field_name in self.fields_dict:
            raise ValueError('Specified register not added to list')
        self.reg_mem.seek(self.fields_dict[field_name].register_offset)
        return struct.unpack('i', self.reg_mem.read(self.bus_width))[0]
