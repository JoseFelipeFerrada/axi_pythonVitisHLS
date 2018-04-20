'''
Module with a bunch of utilities to map memory, access registers and to bitwise operations on them
'''

import os
import mmap
import struct
from collections import namedtuple

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

class UIODevice(object):

	def __init__(self, uio_num = None, base_address = None, map_length = None):
		self.uio_num = uio_num
		self.base_address = base_address
		self.map_length = map_length

	# Override equality operator for unit tests
	def __eq__(self, other):
		return (self.uio_num == other.uio_num and self.base_address == other.base_address and
		self.map_length == other.map_length)


class UIOProber(object):

	UIO_PATH = '/sys/class/uio/'

	def __init__(self):
		self.devices = self.Probe()

	def Probe(self):
		# We need to go through the filesystem to see how many UIO devices we have
		# They are in /sys/class/uio/
		uio_number_list = os.listdir(self.UIO_PATH)
		uio_dict = {}
		# Now we need to fill a dict of UIO devices by going through the dir and getting all relevant information
		for uio_number in uio_number_list:
			uio_dict.update(self.GetUIOInfo(uio_number))
		return uio_dict

	def GetUIOInfo(self, uio_number):
		# Make sure the UIO only has one memory mapped region
		if self.getMapsNumbers(uio_number) > 1:
			raise(NotImplementedError('Modules that map to multiple memory regions are not supported yet'))
		# Start by getting the device name
		ret_dict = {}
		device_name = ''
		with open(self.UIO_PATH + uio_number + '/name') as name_file:
			device_name = name_file.readline().strip()
			ret_dict[device_name] = UIODevice()
		# Assign UIO number
		ret_dict[device_name].uio_num = uio_number
		# Should be default (folder called map0) but better be safe
		map_info_path = self.getMapPath(uio_number) 
		# Get the base_address
		with open(map_info_path + 'addr') as address_file:
			ret_dict[device_name].base_address = int(address_file.readline().strip(), 16)
		# And the mapping length
		with open(map_info_path + 'size') as length_file:
			ret_dict[device_name].map_length = int(length_file.readline().strip(), 16)
		return ret_dict

	# Returns how many memory mapped regions the specified UIO has, if more than one we cannot handle it in this version
	def getMapsNumbers(self, uio_number):
		return len(os.listdir(self.UIO_PATH + uio_number + '/maps'))

	# Returns the path of the folder that describes the memory mapped regions
	def getMapPath(self, uio_number):
		base_path = self.UIO_PATH + uio_number + '/maps/'
		# We now have /sys/class/uio/uio0/maps/
		map_folder = os.listdir(base_path)
		base_path = base_path + map_folder[0] + '/'
		return base_path