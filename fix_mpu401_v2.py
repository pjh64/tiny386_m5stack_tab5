#!/usr/bin/env python3
"""
Correct fix for port 0x330/0x331 (MPU-401 MIDI interface).
Only adds the read handler, writes are ignored by default.
"""

PC_FILE = 'pc.c'

with open(PC_FILE, 'r') as f:
    content = f.read()

# Remove any previous incorrect handlers
import re

# Remove old case 0x330 blocks
content = re.sub(
    r'\tcase 0x330:\n.*?return 0xff;\n',
    '', content, flags=re.DOTALL
)

# Remove old case 0x331 blocks
content = re.sub(
    r'\tcase 0x331:\n.*?return 0x00;\n',
    '', content, flags=re.DOTALL
)

# Remove any write handlers we may have added incorrectly
content = re.sub(
    r'\tcase 0x330:\n.*?return;\n',
    '', content, flags=re.DOTALL
)

content = re.sub(
    r'\tcase 0x331:\n.*?return;\n',
    '', content, flags=re.DOTALL
)

print("Removed old handlers")

# Now add the correct MPU-401 handler ONLY in pc_io_read
# Find "case 0xf1f4:" in the FIRST function (pc_io_read)
# Look for the pattern: this should be in pc_io_read, not pc_io_read_string

# Find the start of pc_io_read function
read_func_start = content.find('static u8 pc_io_read(void *o, int addr)')
if read_func_start == -1:
    print("ERROR: Could not find pc_io_read function")
    exit(1)

# Find the end of pc_io_read (next function starts with "static")
read_func_end = content.find('\nstatic ', read_func_start + 100)
if read_func_end == -1:
    print("ERROR: Could not find end of pc_io_read")
    exit(1)

# Within pc_io_read, find "case 0xf1f4:"
read_func_content = content[read_func_start:read_func_end]
insert_marker = 'case 0xf1f4:'

if insert_marker in read_func_content:
    # Find position relative to full content
    marker_pos = content.find(insert_marker, read_func_start)
    
    mpu401_handler = '''case 0x330:
		// MPU-401 MIDI Data port
		return 0xff;
	case 0x331:
		// MPU-401 MIDI Status port
		// Return 0x00 = all ready (bit 7=0 means "ready to accept")
		// This breaks the polling loop immediately
		return 0x00;
	'''
    
    content = content[:marker_pos] + mpu401_handler + content[marker_pos:]
    print("✓ Added MPU-401 handler in pc_io_read")
else:
    print("WARNING: Could not find insertion point in pc_io_read")

with open(PC_FILE, 'w') as f:
    f.write(content)

print("\n=== Summary ===")
print("Port 0x331 now returns 0x00 (ready) in pc_io_read")
print("No write handler added (writes fall through to default)")
print("\nExpected: LOOP (0xe2) drops from 47.7% to <5%")

