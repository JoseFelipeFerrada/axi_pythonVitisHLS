import re
import json

def parse_registers(filepath):
    """
    Parses a header (.h) file containing register descriptions and definitions
    and returns a JSON string.
    
    Args:
        filepath (str): Path to the header file.
    
    Returns:
        str: JSON string containing parsed register data.
    """
    registers = []
    definitions = {}
    
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Match lines with an address and a colon, e.g., "// 0x10 : Data signal of Kp_PLL"
        reg_match = re.match(r'^//\s*(0x[0-9A-Fa-f]+)\s*:\s*(.*)$', line)
        if reg_match:
            address = reg_match.group(1)
            desc_text = reg_match.group(2).strip()
            
            # If the description indicates "reserved", mark it as such.
            if "reserved" in desc_text.lower():
                entry = {
                    "address": address,
                    "type": "reserved"
                }
            else:
                # Set default values; update if bit information is found.
                entry = {
                    "name": "Unknown",
                    "address": address,
                    "description": desc_text,
                    "access": "Unknown"
                }
                # Check if the next line contains bit information.
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Expected formats:
                    # Data signal:    //        bit 31~0 - Kp_PLL[31:0] (Read/Write)
                    # Control signal: //        bit 0  - Vd_ap_vld (Read/COR)
                    bit_match = re.match(
                        r'^//\s+bit\s+[\d~]+\s*-\s*(\w+)(?:\[\d+:\d+\])?\s*\(([^)]+)\)',
                        next_line
                    )
                    if bit_match:
                        entry["name"] = bit_match.group(1)
                        entry["access"] = bit_match.group(2)
                        entry["address"] = int(entry["address"], 16)
                        i += 1  # Skip the bit line after processing it.
            registers.append(entry)
        i += 1
    
    # Parse #define constants for register addresses.
    for line in lines:
        define_match = re.match(
            r'^#define\s+(X\w+)_CONTROL_ADDR_(\w+)_DATA\s+(0x[0-9A-Fa-f]+)',
            line.strip()
        )
        if define_match:
            macro = define_match.group(1)
            reg_name = define_match.group(2)
            addr = define_match.group(3)
            if macro not in definitions:
                definitions[macro] = {}
            definitions[macro][reg_name] = addr
    
   #Delete resevred by searching dictionaries with the entry keyed "type", other entries do not have this key
    registers = [reg for reg in registers if "type" not in reg]
    registers = {reg["name"]: reg for reg in registers}
    #delete name as entry inside every register
    for reg in registers:
        del registers[reg]["name"]
    
    return registers
