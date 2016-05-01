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

from .model import CpuModelDelegate
from .registers import CORE_REGISTER
from .utilities import (bytes_to_le16, bytes_to_le32, le16_to_bytes, le32_to_bytes)
from collections import namedtuple

MemBuffer = namedtuple('MemBuffer', 'start end data')

class MockCpuModelDelegate(CpuModelDelegate):
    def __init__(self):
        self._mem = []
        self._regs = {reg:0 for reg in CORE_REGISTER.itervalues()}

        # set T bit in xpsr
        self._regs[16] = 0x01000000

    def add_memory(self, start, length):
        buf = MemBuffer(start=start, end=start+length-1, data=bytearray(length))
        self._mem.append(buf)

    def read_register(self, reg):
        return self._regs[reg]

    def write_register(self, reg, value):
        self._regs[reg] = value

    def _find_mem(self, addr):
        for m in self._mem:
            if m.start <= addr <= m.end:
                return m, addr - m.start
        return None, 0

    def read_memory(self, addr, size=32):
        mem, offset = self._find_mem(addr)
        if mem:
            if size == 8:
                return mem.data[offset:offset+1]
            elif size == 16:
                return bytes_to_le16(mem.data[offset:offset+2])
            elif size == 32:
                return bytes_to_le32(mem.data[offset:offset+4])
        return 0

    def write_memory(self, addr, value, size=32):
        mem, offset = self._find_mem(addr)
        if mem:
            if size == 8:
                mem.data[offset:offset+1] = [value]
            elif size == 16:
                mem.data[offset:offset+2] = le16_to_bytes(value)
            elif size == 32:
                mem.data[offset:offset+4] = le32_to_bytes(value)


