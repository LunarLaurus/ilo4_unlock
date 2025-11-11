#!/usr/bin/env python3
#
# This file is part of ilo4_unlock (https://github.com/kendallgoto/ilo4_unlock/).
# Copyright (c) 2022 Kendall Goto
# with some code derived from https://github.com/airbus-seclab/ilo4_toolbox
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
This REPL environment is heavily based on Airbus Security Lab's work.
It produces an SSH-based REPL that allows us to (r)ead/(a)lloc/(w)rite/(f)ree/e(x)ecute
arbitrary code on a running device, patched with our tools. Install 277-tools before using this
REPL!

Notably, we can create new shell commands on-the-fly by performing `wf [source.S]`, which
assembles, allocates and writes custom code to memory.

Use at your own risk.
"""
import keystone
import paramiko
import argparse
import logging
import sys
import time
import struct
import os
from keystone import *
from common import *  # read_patch, hexdump, etc.

"""CONFIG"""
logging.basicConfig(level=logging.DEBUG)
triggerCommand = b'help'
"""END CONFIG"""

def recv_all():
    time.sleep(.05)
    result = b''
    while channel.recv_ready():
        result += channel.recv(4096)
    if result:
        logger.debug("SSH recv: %r", result)
    return result

def recv_force():
    data = recv_all()
    numiter = 0
    while not data:
        numiter += 1
        logger.debug("Waiting ...")
        if numiter <= 10:
            time.sleep(.1)
        else:
            logger.fatal("Time out")
            return b"hpiLO"
        data = recv_all()
    return data

def recv_until_prompt():
    data = recv_force()
    while b'hpiLO' not in data:
        data += recv_force()
    return data

def send(data):
    # Ensure we send bytes
    if isinstance(data, str):
        data = data.encode('ascii')
    logger.debug("SSH send: %r", data)
    channel.send(data)

def srp(d):
    # srp: send and receive prompt
    send(d)
    return recv_until_prompt()

def run_command(cmd):
    # Accept cmd as bytes or str
    if isinstance(cmd, str):
        cmd_b = cmd.encode('ascii')
    else:
        cmd_b = cmd
    result = srp(cmd_b + b'\r')
    needle = b'status_tag=COMMAND COMPLETED\r\n'
    try:
        idx = result.index(needle)
    except ValueError:
        logger.error("run_command: expected completion tag not found in output")
        return b''
    return result[idx+len(needle):].split(b'\n', 4)[-1]

A16_ENCODING = [c.encode('ascii') for c in 'ABCDEFGHIJKLMNOP']

def a16_u8_encode(val):
    """Encode a u8 in alpha-16 encoding"""
    assert 0 <= val <= 0xff
    return A16_ENCODING[val >> 4] + A16_ENCODING[val & 15]

def a16_data_encode(data):
    # ensure data is bytes
    if isinstance(data, str):
        data = data.encode('latin-1')
    return b''.join(a16_u8_encode(struct.unpack('B', data[i:i+1])[0]) for i in range(len(data)))

def a16_u32_encode(val):
    """Encode a u32 in alpha-16 encoding (in Big Endian)"""
    return a16_data_encode(struct.pack('>I', val))

def send_custom(op, arg1, *args):
    arg1 = a16_u32_encode(arg1)
    op_b = op.encode('ascii') if isinstance(op, str) else op
    cmd = triggerCommand + b' ' + op_b + arg1
    if args:
        parts = []
        for a in args:
            if isinstance(a, str):
                parts.append(a.encode('ascii'))
            else:
                parts.append(a)
        cmd += b' ' + b' '.join(parts)
    logger.debug(hexdump(cmd))
    output = srp(cmd + b'\r')
    try:
        cmdindex = output.index(cmd)
    except ValueError:
        # If we can't find the command in the returned output, return entire output trimmed
        output_prefix = output.lstrip(b'\r\n')
        output = output_prefix
    else:
        output_prefix = output[:cmdindex].lstrip(b'\r\n')
        output = output_prefix + output[cmdindex + len(cmd):].lstrip(b'\r\n')
    # cut off last prompt and trailing newlines
    try:
        output = output[:output.rindex(b'hpiLO')].rsplit(b'\n', 1)[0]
    except ValueError:
        pass
    return output.strip(b'\r\n')

def exec_read(cmd):
    if len(cmd) < 3:
        print("r [address] [len]")
        return
    addr = int(cmd[1], 0)
    result = send_custom('r', addr, cmd[2])
    print(hexdump(result))
    print(result)
    return result

def exec_write_partial(addr, data):
    if not data:
        return (0, b'')
    # ensure data is bytes
    if isinstance(data, str):
        data = data.encode('latin-1')
    size = min(len(data), 100)
    output = send_custom('w', addr, a16_data_encode(data[:size]))
    # parse lines from device output
    all_lines = [line.strip() for line in output.decode('ascii', errors='ignore').splitlines() if line not in ('', ' ', '> ', '-> ')]
    if len(all_lines) != size:
        logger.error("Unexpected output line number, got %d expected %d", len(all_lines), size)
    assert len(all_lines) == size
    for i, line in enumerate(all_lines):
        logger.debug(line)
        expected = '%#x <- %#x' % (addr + i, data[i])
        if expected.endswith(' <- 0x0'):
            expected = '%#x <- 0' % (addr + i)
        if expected != line:
            logger.warning("Unexpected write writing 0x%02x to %#x: got %r instead of %r", data[i], addr + i, line, expected)
    return (size, data[size:])

def exec_write(cmd):
    # w [address] [data]
    if len(cmd) < 3:
        print("w [address] [data]")
        return
    addr = int(cmd[1], 0)
    data = cmd[2]
    # if user typed the data as a string, encode to latin-1 to allow 0-255 passthrough
    if isinstance(data, str):
        data = data.encode('latin-1')
    while data:
        size, data = exec_write_partial(addr, data)
        addr += size

def exec_exec(cmd):
    # x [address]
    addr = int(cmd[1], 0)
    print(send_custom('x', addr))

def exec_alloc(cmd):
    # a [size]
    size = int(cmd[1], 0)
    output = send_custom('a', size)
    if output == b'alloc 0':
        logger.error("OUT OF MEMORY")
    prefix = b'alloc 0x'
    assert output.startswith(prefix)
    print(output)
    return int(output[len(prefix):], 16)

def exec_free(cmd):
    # f [address]
    addr = int(cmd[1], 0)
    print(send_custom('f', addr))

def exec_write_file(cmd):
    # wf [file]
    if len(cmd) < 2:
        print("wf [file]")
        return
    try:
        patch = read_patch(cmd[1])
    except Exception:
        logger.error("failed to assemble patch")
        return
    addr = exec_alloc(['a', str(len(patch) + 16)])
    print("allocated 0x%x bytes at 0x%x" % (len(patch) + 16, addr))
    exec_write(['w', "0x%x" % addr, patch])
    print("wrote to 0x%x, execute with x 0x%x" % (addr, addr))

def exec_write_bin(cmd):
    # wb [file]
    if len(cmd) < 2:
        print("wb [file]")
        return
    with open(cmd[1], 'rb') as f:
        patch = f.read()
    addr = exec_alloc(['a', str(len(patch) + 16)])
    print("allocated 0x%x bytes at 0x%x" % (len(patch) + 16, addr))
    exec_write(['w', "0x%x" % addr, patch])
    print("wrote to 0x%x, execute with x 0x%x" % (addr, addr))

def exec_setcmd(cmd):
    # sc [addr]
    if len(cmd) < 2:
        print("sc [addr]")
        return
    addr = int(cmd[1], 0)
    exec_write(['w', "0x000BAB98", struct.pack('<I', addr)])
    print("wrote null_cmd to 0x%x" % addr)

def exec_plain(cmd):
    cmd.pop(0)
    fullcmd = " ".join(cmd)
    # srp expects bytes
    print(srp(fullcmd.encode('ascii') + b'\r'))

parser = argparse.ArgumentParser(description="SSH Tools for iLO4_unlock")
parser.add_argument('addr', help="IP of iLO")
parser.add_argument('-u', '--user', type=str, default='Administrator', help="iLO Username")
parser.add_argument('-p', '--password', type=str, default='', help="iLO Password")
parser.add_argument('-P', '--port', type=int, default=22, help="SSH Port")

args = parser.parse_args()

logger = logging.getLogger('ssh')
logger.info("Connecting ...")
client = paramiko.client.SSHClient()
client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
client.connect(args.addr, args.port, username=args.user, password=args.password, timeout=30, allow_agent=False, look_for_keys=False)

logger.info("SSH session to %s:%d opened", args.addr, args.port)

channel = client.invoke_shell()
channel.setblocking(0)

recv_until_prompt()
run_command(b'show')
logger.info("ready")

try:
    while True:
        cmd_line = input("> ")
        if not cmd_line:
            continue
        cmd = cmd_line.split(' ')
        if cmd[0] == 'r':
            exec_read(cmd)
        elif cmd[0] == 'w':
            exec_write(cmd)
        elif cmd[0] == 'x':
            exec_exec(cmd)
        elif cmd[0] == 'a':
            exec_alloc(cmd)
        elif cmd[0] == 'f':
            exec_free(cmd)
        elif cmd[0] == 'wf':
            exec_write_file(cmd)
        elif cmd[0] == 'wb':
            exec_write_bin(cmd)
        elif cmd[0] == 'sc':
            exec_setcmd(cmd)
        elif cmd[0] == 'z':
            exec_plain(cmd)
        elif cmd[0] == 'exit':
            break
        else:
            print("r/w/x/a/f/wf")
finally:
    if client:
        client.close()
