from axi_python_utilities.register_interface import RegisterInterface

class SampleAXIInterface(RegisterInterface):

	
	def __init__(self, device_name):
		# Base class constructor
		RegisterInterface.__init__(self, device_name)
		# Add registers, first argument is the name, second is the offset in bytes
		# In this case the interface is 32 bits wide so every register is spaced 4 bytes from the following one
		self.AddField('Register_0', 0)
		self.AddField('Register_1', 4)
		# We don't care about Register_2
		self.AddField('Register_3', 12)

	def SetRegister0(self, value):
		self.WriteRegister('Register_0', value)

	def GetRegister0(self):
		return self.ReadRegister('Register_0')


# Simple loopback test
if __name__ == '__main__':
	# device_name should match the one in the Vivado project / device tree
	dev = SampleAXIInterface('axi4_read')
	sample_val = 0x12345678
	print("Writing " + str(sample_val))
	dev.SetRegister0(sample_val)
	read_val = dev.GetRegister0()
	print("Read " + str(read_val))
	if read_val == sample_val:
		print("Loopback test success")
	else:
		print("Loopback test failed")