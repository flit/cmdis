#!/usr/bin/env python

# Copyright (c) 2016 Chris Reed
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# o Redistributions of source code must retain the above copyright notice, this list
#   of conditions and the following disclaimer.
#
# o Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# o Neither the names of the copyright holders nor the names of the
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function
from .registers import register_name_to_index
from .utilities import (bfi, bfx)
from .bitstring import bitstring
import six
import logging

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

##
# @brief
#
# All register and integer values are passed as bitstrings.
class CpuModel(object):
    def __init__(self):
        self._delegate = None
        self._registers_interface = RegistersInterface(self, 0, 15)
        self._float_registers_interface = RegistersInterface(self, 0x40, 0x5f)
        self._apsr = ApsrAlias(self)

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
    def pc(self):
        return self.read_register('pc')
#         return bitstring(self.read_register('pc').unsigned + 4)

    @pc.setter
    def pc(self, value):
        self.write_register('pc', value)

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
        if self._delegate is not None:
            return bitstring(self._delegate.read_memory(addr, size), size)

    def write_memory(self, addr, value, size=32):
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
        return "<%s@%s pc=%x xpsr=%x>" % (self.__class__.__name__, hex(id(self)), self.pc, self.xpsr)

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


