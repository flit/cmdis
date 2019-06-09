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

from __future__ import print_function
from enum import Enum
import six
import logging

from .registers import register_name_to_index
from .utilities import (bfi, bfx)
from .bitstring import bitstring

class RegistersInterface(object):
    def __init__(self, cpu, first, last):
        self._cpu = cpu
        self._first = first
        self._last = last

    def __getitem__(self, key):
        index = self._first + key
        if self._first + index > self._last:
            raise KeyError("out of range register index %d" % key)
        return self._cpu.read_register(self._first + index)

    def __setitem__(self, key, value):
        index = self._first + key
        if index > self._last:
            raise KeyError("out of range register index %d" % key)
        self._cpu.write_register(index, value)

class ApsrAlias(object):
    N_BIT = 31
    Z_BIT = 30
    C_BIT = 29
    V_BIT = 28

    def __init__(self, cpu):
        self._cpu = cpu

    @property
    def n(self):
        return self._cpu.xpsr[self.N_BIT]

    @n.setter
    def n(self, value):
        v = self._cpu.xpsr
        v[self.N_BIT] = bitstring(value, 1)
        self._cpu.xpsr = v

    @property
    def z(self):
        return self._cpu.xpsr[self.Z_BIT]

    @z.setter
    def z(self, value):
        v = self._cpu.xpsr
        v[self.Z_BIT] = bitstring(value, 1)
        self._cpu.xpsr = v

    @property
    def c(self):
        return self._cpu.xpsr[self.C_BIT]

    @c.setter
    def c(self, value):
        v = self._cpu.xpsr
        v[self.C_BIT] = bitstring(value, 1)
        self._cpu.xpsr = v

    @property
    def v(self):
        return self._cpu.xpsr[self.V_BIT]

    @v.setter
    def v(self, value):
        v = self._cpu.xpsr
        v[self.V_BIT] = bitstring(value, 1)
        self._cpu.xpsr = v

class CpuMode(Enum):
    Thread = 0
    Handler = 1

##
# @brief
#
# All register and integer values are passed as bitstrings.
#
# TODO handle CPU features better
class CpuModel(object):
    nPRIV = 0
    SPSEL = 1
    FPCA = 2

    def __init__(self):
        self._delegate = None
        self._registers_interface = RegistersInterface(self, 0, 15)
        self._float_registers_interface = RegistersInterface(self, 0x40, 0x5f)
        self._apsr = ApsrAlias(self)
        self._mode = CpuMode.Thread

    @property
    def has_dsp_ext(self):
        return False

    @property
    def has_fp_ext(self):
        return False

    @property
    def delegate(self):
        return self._delegate

    @delegate.setter
    def delegate(self, newDelegate):
        self._delegate = newDelegate

    def execute(self, instructions):
        for i in instructions:
            i.execute(self)

    @property
    def in_it_block(self):
        return False

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, newMode):
        # TODO handle mode transitions correctly
        self._mode = newMode

    @property
    def pc(self):
        return self.read_register('pc')

    @pc.setter
    def pc(self, value):
        self.write_register('pc', value)

    ## @brief Returns PC + 4 used in instruction implementations.
    @property
    def pc_for_instr(self):
        return self.read_register('pc') + 4

    @property
    def lr(self):
        return self.read_register('lr')

    @lr.setter
    def lr(self, value):
        self.write_register('lr', value)

    @property
    def sp(self):
        return self.read_register('sp');

    @sp.setter
    def sp(self, value):
        self.write_register('sp', value)

    @property
    def msp(self):
        return self.read_register('msp');

    @msp.setter
    def msp(self, value):
        self.write_register('msp', value)

    @property
    def psp(self):
        return self.read_register('psp')

    @psp.setter
    def psp(self, value):
        self.write_register('psp', value)

    @property
    def control(self):
        return self.read_register('control')

    @property
    def is_privileged(self):
        return self.control[self.nPRIV] == '0'

    @property
    def xpsr(self):
        return self.read_register('xpsr')

    @xpsr.setter
    def xpsr(self, value):
        self.write_register('xpsr', value)

    @property
    def apsr(self):
        return self._apsr

    @property
    def ipsr(self):
        return self.xpsr[0:6]

    @property
    def r(self):
        return self._registers_interface

    @property
    def s(self):
        return self._float_registers_interface

    def read_register(self, reg):
        reg = register_name_to_index(reg)
        if self._delegate is not None:
            return bitstring(self._delegate.read_register(reg))

    def write_register(self, reg, value):
        reg = register_name_to_index(reg)
        if isinstance(value, bitstring):
            value = value.unsigned
        if self._delegate is not None:
            self._delegate.write_register(reg, value)

    def read_memory(self, addr, size=32):
        if isinstance(addr, bitstring):
            addr = addr.unsigned
        if self._delegate is not None:
            return bitstring(self._delegate.read_memory(addr, size), size)

    def write_memory(self, addr, value, size=32):
        if isinstance(addr, bitstring):
            addr = addr.unsigned
        if isinstance(value, bitstring):
            value = value.unsigned
        if self._delegate is not None:
            self._delegate.write_memory(addr, value, size)

    def read32(self, addr):
        return self.read_memory(addr, 32)

    def read16(self, addr):
        return self.read_memory(addr, 16)

    def read8(self, addr):
        return self.read_memory(addr, 8)

    def write32(self, addr, value):
        return self.write_memory(addr, value, 32)

    def write16(self, addr, value):
        return self.write_memory(addr, value, 16)

    def write8(self, addr, value):
        return self.write_memory(addr, value, 8)

    def write_memory_block(self, addr, data):
        if self._delegate is not None:
            self._delegate.write_memory_block(addr, data)

    def read_memory_block(self, addr, length):
        if self._delegate is not None:
            return self._delegate.read_memory_block(addr, length)

    def dump(self):
        print("r0=%08x    r4=%08x    r8 =%08x   r12=%08x" % (
            self.r[0], self.r[4], self.r[8], self.r[12]))
        print("r1=%08x    r5=%08x    r9 =%08x   sp =%08x" % (
            self.r[1], self.r[5], self.r[9], self.sp))
        print("r2=%08x    r6=%08x    r10=%08x   lr =%08x" % (
            self.r[2], self.r[6], self.r[10], self.lr))
        print("r3=%08x    r7=%08x    r11=%08x   pc =%08x" % (
            self.r[3], self.r[7], self.r[11], self.pc))

    def __repr__(self):
        return "<%s@%s pc=%x xpsr=%x rN=[%s]>" % \
            (self.__class__.__name__, hex(id(self)), self.pc, self.xpsr,
            " ".join("%x" % (self.r[i].unsigned) for i in range(15)))

##
# Register and memory values in the delegate APIs are all regular integers.
class CpuModelDelegate(object):
    def __init__(self):
        pass

    def read_register(self, reg):
        pass

    def write_register(self, reg, value):
        pass

    def read_memory(self, addr, size=32):
        pass

    def write_memory(self, addr, value, size=32):
        pass


