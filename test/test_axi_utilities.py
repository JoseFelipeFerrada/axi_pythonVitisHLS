'''
Test module for AXI utilities
'''

# Imports to add library to path
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../axi_python_utilities")

import unittest
from register_interface import RegisterInterface
from uio_utilities import  UIOProber, UIODevice

# CHANGE THIS based on hardware
NUM_UIO_DEVICES = 6
# A device that we can do loopback test on register 0
TEST_UIO_DEVICE_NAME = 'axi4_read'
# Manually filled device for testing purposes
TEST_DEVICE = UIODevice(uio_num = 'uio0', base_address = 0x43C10000, map_length = 0x10000)

class TestAxiUtilities(unittest.TestCase):

    def setUp(self):
        # Use axi4 read as a test
        self.device_name = TEST_UIO_DEVICE_NAME
        self.reg_length = 64*1024
        self.regint = RegisterInterface(self.device_name)
        # self.test_address = 0x38000000
        # self.transfer_length = 4096

    # Noop, just run setUp
    def test_object_creation(self):
        pass

    def test_mmap(self):
        # Can map the DMA access memory
        self.assertEqual(len(self.regint.reg_mem), self.reg_length)

    def test_unimplemented_register(self):
        # Registers below a whole bus width data size are not implemented yet
        self.assertRaises(NotImplementedError, self.regint.AddField, 'test_reg', 12, 5, 1)

    def test_addfield_paramcheck(self):
        # We try to add a field with wrong parameters
        # General negative numbers
        self.assertRaises(ValueError, self.regint.AddField, 'test_reg', 10, 1, -1)
        self.assertRaises(ValueError, self.regint.AddField, 'test_reg', -1, 1, 1)
        self.assertRaises(ValueError, self.regint.AddField, 'test_reg', 10, -1, 1)
        # More bits than the register can contain!
        self.assertRaises(ValueError, self.regint.AddField, 'test_reg', 12, 4, 6)
        # Invalid register offset (not multiple of bus width)
        self.assertRaises(ValueError, self.regint.AddField, 'test_reg', 11, 4, 1)
        # Invalid offset (greater than width)
        self.assertRaises(ValueError, self.regint.AddField, 'test_reg', 12, 32, 1)
        # Register already present
        self.regint.AddField('test_reg', 8)
        self.assertRaises(ValueError, self.regint.AddField, 'test_reg', 12, 4, 1)

    def test_addfield_default(self):
        # Check that we can call without specifying bit parameters for whole register addressing
        self.regint.AddField('test_reg_default', 0)

    def test_setbits(self):
        self.assertEqual(self.regint.SetBits(0x100,2,1), 0x104)
        self.assertEqual(self.regint.SetBits(0x101,0,1), 0x101)
        # Multiple bits
        self.assertEqual(self.regint.SetBits(0x000,3,4), 0x00F)
        self.assertEqual(self.regint.SetBits(0x000,3,3), 0x00E)
            

    def test_clearbits(self):
        self.assertEqual(self.regint.ClearBits(0x108,3,1), 0x100)
        self.assertEqual(self.regint.ClearBits(0x100,5,1), 0x100)
        # Multiple bits
        self.assertEqual(self.regint.ClearBits(0x00F,3,4), 0x000)
        self.assertEqual(self.regint.ClearBits(0x00F,3,3), 0x001)

    def test_writeregister_noreg(self):
        self.assertRaises(ValueError, self.regint.WriteRegister, 'nonexisting_reg', 10)

    def test_writeregister_outofbounds(self):
        self.regint.AddField('existing_reg', 0)
        self.assertRaises(ValueError, self.regint.WriteRegister, 'existing_reg', 2**32)

    def test_writeregister(self):
        self.regint.AddField('existing_reg', 0, 31, 32)
        self.regint.WriteRegister('existing_reg', 10)

    def test_readregister_noreg(self):
        self.assertRaises(ValueError, self.regint.ReadRegister, 'nonexisting_reg')

    def test_writeregister_loopback(self):
        # Loopback, meaning write a value and read it back
        self.regint.AddField('test_reg', 0)
        tmp_val = self.regint.ReadRegister('test_reg')
        tmp_val = tmp_val + 1
        self.regint.WriteRegister('test_reg', tmp_val)
        self.assertEqual(self.regint.ReadRegister('test_reg'), tmp_val)

# Same as above but without setup
class TestUIOErrors(unittest.TestCase):

    def test_nonexistingdevice(self):
        self.assertRaises(KeyError, RegisterInterface, 'NONEXISTINGDEVICE')


class TestProber(unittest.TestCase):

    def setUp(self):
        self.prober = UIOProber()

    # Noop, just run setUp
    def test_object_creation(self):
        pass

    # Check that we have the correct numbe
    def test_num_devices(self):
        self.assertEqual(len(self.prober.devices), NUM_UIO_DEVICES)

    # Make sure we have UIO devices as a return type
    def test_device_type(self):
        self.assertIsInstance(self.prober.devices, dict)

    def test_UIOInfo_returntype(self):
        ret_val = self.prober.GetUIOInfo('uio0')
        self.assertIsInstance(ret_val, dict)
        self.assertIsInstance(ret_val['axi4_read'], UIODevice)

    # And make sure the values are correct
    def test_UIOInfo_returnvalue(self):
        self.assertEqual(self.prober.GetUIOInfo('uio0')['axi4_read'], TEST_DEVICE)

    # Test the getMapsNumbers, if we have more than one map this library will not work for now
    def test_getmapsnumbers(self):
        self.assertEqual(self.prober.getMapsNumbers('uio0'), 1)

    def test_getmappath(self):
        self.assertEqual(self.prober.getMapPath('uio0'), '/sys/class/uio/uio0/maps/map0/')

    # Finally check that the struct for our axi4_read device is in the list
    def test_uiolist(self):
        self.assertEqual(self.prober.devices['axi4_read'], TEST_DEVICE)


if __name__ == '__main__':
    unittest.main()
