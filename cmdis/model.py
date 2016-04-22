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

import six
import logging
from .registers import register_name_to_index

class RegistersInterface(object):
    def __init__(self, cpu):
        self._cpu = cpu

    def __getitem__(self, key):
        return self._cpu.read_register(key)

    def __setitem__(self, key, value):
        self._cpu.write_register(key, value)

##
# @brief
class CpuModel(object):
    def __init__(self):
        self._delegate = None
        self._registers_interface = RegistersInterface(self)

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
    def pc(self):
        return self.read_register('pc') + 4

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
    def r(self):
        return self._registers_interface

    def read_register(self, reg):
        reg = register_name_to_index(reg)
        if self._delegate is not None:
            return self._delegate.read_register(reg)

    def write_register(self, reg, value):
        reg = register_name_to_index(reg)
        if self._delegate is not None:
            self._delegate.write_register(reg, value)

    def read_memory(self, addr, size=32):
        if self._delegate is not None:
            return self._delegate.read_memory(addr, size)

    def write_memory(self, addr, value, size=32):
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


