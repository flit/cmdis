#!/usr/bin/env python

# Copyright (c) 2016-2019 Chris Reed
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging
import os
import sys
import optparse
from optparse import make_option
import traceback
try:
    import gnureadline
except ImportError:
    pass

import cmdis
from cmdis import __version__
import cmdis.model
import cmdis.disasm
import cmdis.registers
import cmdis.mock_cpu

LEVELS = {
        'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR,
        'critical':logging.CRITICAL
        }

## Command info and help.
COMMAND_INFO = {
        'info' : {
            'aliases' : ['i'],
            'args' : "",
            'help' : "Display target type and IDs"
            },
        'status' : {
            'aliases' : ['stat'],
            'args' : "",
            'help' : "Show the target's current state"
            },
        'reg' : {
            'aliases' : [],
            'args' : "[REG]",
            'help' : "Print all or one register"
            },
        'wreg' : {
            'aliases' : [],
            'args' : "REG VALUE",
            'help' : "Set the value of a register"
            },
        'reset' : {
            'aliases' : [],
            'args' : "[-h/--halt]",
            'help' : "Reset the target"
            },
        'read8' : {
            'aliases' : ['read', 'r', 'rb'],
            'args' : "ADDR [LEN]",
            'help' : "Read 8-bit bytes"
            },
        'read16' : {
            'aliases' : ['r16', 'rh'],
            'args' : "ADDR [LEN]",
            'help' : "Read 16-bit halfwords"
            },
        'read32' : {
            'aliases' : ['r32', 'rw'],
            'args' : "ADDR [LEN]",
            'help' : "Read 32-bit words"
            },
        'write8' : {
            'aliases' : ['write', 'w', 'wb'],
            'args' : "ADDR DATA...",
            'help' : "Write 8-bit bytes"
            },
        'write16' : {
            'aliases' : ['w16', 'wh'],
            'args' : "ADDR DATA...",
            'help' : "Write 16-bit halfwords"
            },
        'write32' : {
            'aliases' : ['w32', 'ww'],
            'args' : "ADDR DATA...",
            'help' : "Write 32-bit words"
            },
        'step' : {
            'aliases' : ['s'],
            'args' : "",
            'help' : "Step one instruction"
            },
        'help' : {
            'aliases' : ['?'],
            'args' : "[CMD]",
            'help' : "Show help for commands"
            },
        'disasm' : {
            'aliases' : ['d'],
            'args' : "[-c/--center] ADDR [LEN]",
            'help' : "Disassemble instructions at an address"
            },
        'log' : {
            'aliases' : [],
            'args' : "LEVEL",
            'help' : "Set log level to one of debug, info, warning, error, critical"
            },
        'exit' : {
            'aliases' : ['quit'],
            'args' : "",
            'help' : "Quit the simulator"
            },
        }

def hex_width(value, width):
    if width == 8:
        return "%02x" % value
    elif width == 16:
        return "%04x" % value
    elif width == 32:
        return "%08x" % value
    else:
        raise ToolError("unrecognized register width (%d)" % reg.size)

def dumpHexData(data, startAddress=0, width=8):
    i = 0
    while i < len(data):
        print "%08x: " % (startAddress + i),

        while i < len(data):
            d = data[i]
            i += 1
            if width == 8:
                print "%02x" % d,
                if i % 4 == 0:
                    print "",
                if i % 16 == 0:
                    break
            elif width == 16:
                print "%04x" % d,
                if i % 8 == 0:
                    break
            elif width == 32:
                print "%08x" % d,
                if i % 4 == 0:
                    break
        print

class ToolError(Exception):
    pass

class ToolExitException(Exception):
    pass

def cmdoptions(opts):
    def process_opts(fn):
        parser = optparse.OptionParser(add_help_option=False)
        for opt in opts:
            parser.add_option(opt)
        def foo(inst, args):
            namespace, other_args = parser.parse_args(args)
            return fn(inst, namespace, other_args)
        return foo
    return process_opts

class SimConsole(object):
    PROMPT = '>>> '

    def __init__(self, tool):
        self.tool = tool
        self.last_command = ''

    def run(self):
        try:
            while True:
                try:
                    line = raw_input(self.PROMPT)
                    line = line.strip()
                    if line:
                        self.process_command_line(line)
                        self.last_command = line
                    elif self.last_command:
                        self.process_command(self.last_command)
                except KeyboardInterrupt:
                    print
        except EOFError:
            # Print a newline when we get a Ctrl-D on a Posix system.
            # Windows exits with a Ctrl-Z+Return, so there is no need for this.
            if os.name != "nt":
                print

    def process_command_line(self, line):
        for cmd in line.split(';'):
            self.process_command(cmd)

    def process_command(self, cmd):
        try:
            if (cmd.strip())[0] == '$':
                cmd = cmd[1:].strip()
                self.tool.handle_python(cmd)
                return

            args = cmd.split()
            cmd = args[0].lower()
            args = args[1:]

            # Handle help.
            if cmd in ['?', 'help']:
                self.show_help(args)
                return

            # Handle register name as command.
            if cmd in cmdis.registers.CORE_REGISTER:
                self.tool.handle_reg([cmd])
                return

            # Check for valid command.
            if cmd not in self.tool.command_list:
                print "Error: unrecognized command '%s'" % cmd
                return

            # Run command.
            handler = self.tool.command_list[cmd]
            handler(args)
        except ValueError:
            print "Error: invalid argument"
            traceback.print_exc()
        except ToolError as e:
            print "Error:", e
        except ToolExitException:
            raise
        except Exception as e:
            print "Unexpected exception:", e
            traceback.print_exc()

    def show_help(self, args):
        if not args:
            self.list_commands()

    def list_commands(self):
        cmds = sorted(COMMAND_INFO.keys())
        print "Commands:\n---------"
        for cmd in cmds:
            info = COMMAND_INFO[cmd]
            print "{cmd:<25} {args:<20} {help}".format(
                cmd=', '.join(sorted([cmd] + info['aliases'])),
                **info)
        print
        print "All register names are also available as commands that print the register's value."
        print "Any ADDR or LEN argument will accept a register name."

class SimTool(object):
    def __init__(self):
        self.board = None
        self.exitCode = 0
        self.command_list = {
                'info' :    self.handle_info,
                'i' :       self.handle_info,
                'reg' :     self.handle_reg,
                'wreg' :    self.handle_write_reg,
                'reset' :   self.handle_reset,
                'read' :    self.handle_read8,
                'read8' :   self.handle_read8,
                'read16' :  self.handle_read16,
                'read32' :  self.handle_read32,
                'r' :       self.handle_read8,
                'rb' :      self.handle_read8,
                'r16' :     self.handle_read16,
                'rh' :      self.handle_read16,
                'r32' :     self.handle_read32,
                'rw' :      self.handle_read32,
                'write' :   self.handle_write8,
                'write8' :  self.handle_write8,
                'write16' : self.handle_write16,
                'write32' : self.handle_write32,
                'w' :       self.handle_write8,
                'wb' :      self.handle_write8,
                'w16' :     self.handle_write16,
                'wh' :      self.handle_write16,
                'w32' :     self.handle_write32,
                'ww' :      self.handle_write32,
                'step' :    self.handle_step,
                's' :       self.handle_step,
                'disasm' :  self.handle_disasm,
                'd' :       self.handle_disasm,
                'map' :     self.handle_memory_map,
                'log' :     self.handle_log,
                'exit' :    self.handle_exit,
                'quit' :    self.handle_exit,
            }

    def get_args(self):
        debug_levels = LEVELS.keys()

        parser = argparse.ArgumentParser(description='Cortex-M interactive simulator', epilog='')
        parser.add_argument('--version', action='version', version=__version__)
        parser.add_argument("-d", "--debug", dest="debug_level", choices=debug_levels, default='warning', help="Set the level of system logging output. Supported choices are: " + ", ".join(debug_levels), metavar="LEVEL")
        parser.add_argument("binary_file", nargs='?', type=argparse.FileType('rb'), help="Optional binary file to simulate.")
        return parser.parse_args()

    def configure_logging(self):
        level = LEVELS.get(self.args.debug_level, logging.WARNING)
        logging.basicConfig(level=level)

    def create_sim(self):
        self.cpu = cmdis.model.CpuModel()
        self.cpu.delegate = cmdis.mock_cpu.MockCpuModelDelegate()

        # Add fake flash containing the binary file.
        self.cpu.delegate.add_memory(0, max(0x10000, len(self.binary_data)))
        self.cpu.write_memory_block(0, self.binary_data)

        # Add fake ram region. Make sure it includes the stack pointer.
        sp = self.cpu.read32(0).unsigned
        if sp != 0:
            ramsize = max(sp - 0x1fff8000, 0x10000)
        else:
            ramsize = 0x10000
        self.cpu.delegate.add_memory(0x1fff8000, ramsize)

    def reset_sim(self):
        pc = self.cpu.read32(4)
        mem, offset = self.cpu.delegate._find_mem(pc.unsigned)
        if mem:
            self.cpu.pc = pc

        sp = self.cpu.read32(0)
        mem, offset = self.cpu.delegate._find_mem(sp.unsigned - 4)
        if mem:
            self.cpu.sp = sp

        print "CPU model reset.\nPC = 0x%08x\nSP = 0x%08x" % (pc, sp)

    def run(self):
        try:
            # Read command-line arguments.
            self.args = self.get_args()

            # Read the binary file.
            if self.args.binary_file is not None:
                try:
                    self.binary_data = self.args.binary_file.read()
                finally:
                    self.args.binary_file.close()
            else:
                self.binary_data = ''

            # Set logging level
            self.configure_logging()

            # Set up simulator.
            self.create_sim()
            self.reset_sim()

            # Enter interactive mode.
            console = SimConsole(self)
            console.run()

        except ToolExitException:
            self.exitCode = 0
        except ValueError:
            print "Error: invalid argument"
        except ToolError as e:
            print "Error:", e
            self.exitCode = 1
        finally:
            if self.board != None:
                # Pass false to prevent target resume.
                self.board.uninit(False)

        return self.exitCode

    def handle_info(self, args):
        print ""

    def handle_reg(self, args):
        # If there are no args, print all register values.
        if len(args) < 1:
            self.dump_registers()
            return

        reg = args[0].lower()
        if reg in cmdis.registers.CORE_REGISTER:
            value = self.cpu.read_register(reg)
            print "%s = 0x%08x (%d)" % (reg, value, value)
        else:
            raise ToolError("invalid register '%s'" % (reg))

    def handle_write_reg(self, args):
        if len(args) < 1:
            raise ToolError("No register specified")
        if len(args) < 2:
            raise ToolError("No value specified")

        reg = args[0].lower()
        value = self.convert_value(args[1])
        self.cpu.write_register(reg, value)

    def handle_reset(self, args, other):
        self.reset_sim()

    @cmdoptions([make_option('-c', "--center", action="store_true")])
    def handle_disasm(self, args, other):
        if len(other) == 0:
            other = ['pc']
        addr = self.convert_value(other[0])
        if len(other) < 2:
            count = 6
        else:
            count = self.convert_value(other[1])

        if args.center:
            addr -= count // 2

        # Since we're disassembling, make sure the Thumb bit is cleared.
        addr &= ~1

        # Print disasm of data.
        data = self.cpu.read_memory_block(addr, count)
        self.print_disasm(data, addr)

    def handle_read8(self, args):
        return self.do_read(args, 8)

    def handle_read16(self, args):
        return self.do_read(args, 16)

    def handle_read32(self, args):
        return self.do_read(args, 32)

    def handle_write8(self, args):
        return self.do_write(args, 8)

    def handle_write16(self, args):
        return self.do_write(args, 16)

    def handle_write32(self, args):
        return self.do_write(args, 32)

    def do_read(self, args, width):
        if len(args) == 0:
            print "Error: no address specified"
            return 1
        addr = self.convert_value(args[0])
        if len(args) < 2:
            count = width // 8
        else:
            count = self.convert_value(args[1])

        if width == 8:
            data = self.cpu.read_memory_block(addr, count)
            byteData = data
        elif width == 16:
            byteData = self.cpu.read_memory_block(addr, count)
            data = cmdis.utilities.byteListToU16leList(byteData)
        elif width == 32:
            byteData = self.cpu.read_memory_block(addr, count)
            data = cmdis.utilities.byteListToU32leList(byteData)

        # Print hex dump of output.
        dumpHexData(data, addr, width=width)

    def do_write(self, args, width):
        if len(args) == 0:
            print "Error: no address specified"
            return 1
        addr = self.convert_value(args[0])
        if len(args) <= 1:
            print "Error: no data for write"
            return 1
        else:
            data = bytearray(self.convert_value(d) for d in args[1:])

        if width == 8:
            pass
        elif width == 16:
            data = bytearray(cmdis.utilities.u16leListToByteList(data))
        elif width == 32:
            data = bytearray(cmdis.utilities.u32leListToByteList(data))

        self.cpu.write_memory_block(addr, data)

    def handle_step(self, args):
        pc = self.cpu.read_register('pc').unsigned & ~1

        dis = cmdis.disasm.Disassembler()
        fmt = cmdis.formatter.Formatter(self.cpu)

        try:
            code = self.cpu.read_memory_block(pc, 4)
            ilist = [i for i in dis.disasm(code, pc)]

            if not len(ilist):
                print "No instructions found!"
                return

            # Only use the first instruction.
            i = ilist[0]

            print "{addr:#010x}:  {instr}".format(addr=i.address, instr=fmt.format(i))

            i.execute(self.cpu)

        except cmdis.decoder.UndefinedInstructionError:
            print "Undefined instruction"

    def handle_memory_map(self, args):
        self.print_memory_map()

    def handle_log(self, args):
        if len(args) < 1:
            print "Error: no log level provided"
            return 1
        if args[0].lower() not in LEVELS:
            print "Error: log level must be one of {%s}" % ','.join(LEVELS.keys())
            return 1
        logging.getLogger().setLevel(LEVELS[args[0].lower()])

    def handle_exit(self, args):
        raise ToolExitException()

    def handle_python(self, args):
        try:
            env = {
                    'cpu' : self.cpu,
                }
            result = eval(args, globals(), env)
            if result is not None:
                if type(result) is int:
                    print "0x%08x (%d)" % (result, result)
                else:
                    print result
        except Exception as e:
            print "Exception while executing expression:", e
            traceback.print_exc()

    ## @brief Convert an argument to a 32-bit integer.
    #
    # Handles the usual decimal, binary, and hex numbers with the appropriate prefix.
    # Also recognizes register names and address dereferencing. Dereferencing using the
    # ARM assembler syntax. To dereference, put the value in brackets, i.e. '[r0]' or
    # '[0x1040]'. You can also use put an offset in the brackets after a comma, such as
    # '[r3,8]'. The offset can be positive or negative, and any supported base.
    def convert_value(self, arg):
        arg = arg.lower().replace('_', '')
        deref = (arg[0] == '[')
        if deref:
            arg = arg[1:-1]
            offset = 0
            if ',' in arg:
                arg, offset = arg.split(',')
                arg = arg.strip()
                offset = int(offset.strip(), base=0)

        if arg in cmdis.registers.CORE_REGISTER:
            value = self.cpu.read_register(arg).unsigned
            print "%s = 0x%08x" % (arg, value)
        else:
            value = int(arg, base=0)

        if deref:
            value = cmdis.utilities.bytes_to_le32(self.cpu.read_memory_block(value + offset, 4))
            print "[%s,%d] = 0x%08x" % (arg, offset, value)

        return value

    def dump_registers(self):
        # Registers organized into columns for display.
        regs = [['r0', 'r6', 'r12', 'xpsr'],
                ['r1', 'r7', 'sp', 'control'],
                ['r2', 'r8', 'lr', 'primask'],
                ['r3', 'r9', 'pc', 'faultmask'],
                ['r4', 'r10', 'msp', 'basepri'],
                ['r5', 'r11', 'psp']]

        for row in regs:
            for colnum, reg in enumerate(row):
                regValue = self.cpu.read_register(reg)
                if colnum == 3:
                    fmt = "{:>10} {:#010x} "
                else:
                    fmt = "{:>4} {:#010x} "
                print fmt.format(reg + ':', regValue.unsigned),
            print

    def print_memory_map(self):
        pass
#         print "Region          Start         End           Blocksize"
#         for region in self.target.getMemoryMap():
#             print "{:<15} {:#010x}    {:#010x}    {}".format(region.name, region.start, region.end, region.blocksize if region.isFlash else '-')

    def print_disasm(self, code, startAddr):
        pc = self.cpu.read_register('pc').unsigned & ~1

        dis = cmdis.disasm.Disassembler()
        fmt = cmdis.formatter.Formatter(self.cpu)

        addrLine = 0
        text = ''
        try:
            for i in dis.disasm(code, startAddr):
                pc_marker = '*' if (pc == i.address) else ' '
                text += "{addr:#010x}:{pc_marker} {instr}\n".format(addr=i.address, pc_marker=pc_marker, instr=fmt.format(i))

#                 hexBytes = ''
#                 for b in i.bytes:
#                     hexBytes += '%02x' % b
#                 text += "{addr:#010x}:{pc_marker} {bytes:<10}{mnemonic:<8}{args}\n".format(addr=i.address, pc_marker=pc_marker, bytes=hexBytes, mnemonic=i.mnemonic, args=i.op_str)
        except cmdis.decoder.UndefinedInstructionError:
            print "Undefined instruction"
        if text[-1] == '\n':
            text = text[:-1]
        print text


def main():
    sys.exit(SimTool().run())


if __name__ == '__main__':
    main()
