import os

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