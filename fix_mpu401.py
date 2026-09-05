#!/usr/bin/env python3
"""
Fixes port 0x330/0x331 (MPU-401 MIDI interface).

MPU-401 Status Register (0x331):
  Bit 7: 1 = NOT ready (busy), 0 = ready
  Bit 6: 1 = NOT ready, 0 = ready to accept command

Previous fix returned 0x80 (bit 7 SET = "not ready"), causing infinite polling.
Correct fix: return 0x00 (all ready bits clear) to break the polling loop.
"""

PC_FILE = 'pc.c'

with open(PC_FILE, 'r') as f:
    content = f.read()

# First, remove any previous 0x331/0x330 handlers we may have added
import re

# Remove old case 0x330 block if present
content = re.sub(
    r'\tcase 0x330:\n\t\t// Floppy Controller Digital Output Register.*?return 0x1c;.*?\n',
    '', content, flags=re.DOTALL
)

# Remove old case 0x331 block if present  
content = re.sub(
    r'\tcase 0x331:\n\t\t// Floppy Controller Main Status Register.*?return floppy_status_value;\n\t\t\}\n',
    '', content, flags=re.DOTALL
)

# Also remove any simpler 0x331 handler
content = re.sub(
    r'\tcase 0x331:\n.*?return 0x80;.*?\n',
    '', content, flags=re.DOTALL
)

# Remove floppy variables if present
content = re.sub(
    r'\n// === FLOPPY CONTROLLER OPTIMIZATION ===.*?// === END FLOPPY CONTROLLER OPTIMIZATION ===\n',
    '\n', content, flags=re.DOTALL
)

print("Removed old 0x330/0x331 handlers")

# Now add the correct MPU-401 handler in pc_io_read
# Find the right place to insert (before the default case in pc_io_read)

# Find "case 0xf1f4:" which is near the end of pc_io_read
insert_marker = 'case 0xf1f4:'
if insert_marker in content:
    insert_pos = content.find(insert_marker)
    
    mpu401_handler = '''case 0x330:
		// MPU-401 MIDI Data port
		return 0xff;
	case 0x331:
		// MPU-401 MIDI Status port
		// Return 0x00 = all ready (bit 7=0 means "ready to accept")
		// This breaks the polling loop immediately
		return 0x00;
	'''
    
    content = content[:insert_pos] + mpu401_handler + content[insert_pos:]
    print("Added MPU-401 handler in pc_io_read")
else:
    print("WARNING: Could not find insertion point in pc_io_read")

# Also handle writes to 0x331 in pc_io_write
# Find the default case in pc_io_write
write_marker = 'case 0xf1f4:'
# Find the SECOND occurrence (in pc_io_write)
first_pos = content.find(write_marker)
if first_pos != -1:
    second_pos = content.find(write_marker, first_pos + 1)
    if second_pos != -1:
        mpu401_write = '''case 0x330:
		// MPU-401 MIDI Data write - ignore
		return;
	case 0x331:
		// MPU-401 MIDI Command write - acknowledge
		return;
	'''
        content = content[:second_pos] + mpu401_write + content[second_pos:]
        print("Added MPU-401 handler in pc_io_write")

with open(PC_FILE, 'w') as f:
    f.write(content)

print("\n=== Summary ===")
print("Port 0x331 now returns 0x00 (ready) instead of 0x80 (not ready)")
print("This should break the infinite polling loop")
print("\nExpected: LOOP (0xe2) drops from 47.7% to <5%")

