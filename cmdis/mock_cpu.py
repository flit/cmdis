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
        # Special restrictions for CONTROL register writes.
        if reg in (CORE_REGISTER['faultmask'], CORE_REGISTER['primask']):
            value = value & 1
        elif reg == CORE_REGISTER['basepri']:
            value = value & 0xff
        elif reg in (CORE_REGISTER['sp'], CORE_REGISTER['msp'], CORE_REGISTER['psp']):
            value = value & ~3
        self._regs[reg] = value

        # Mirror SP writes to PSP/MSP and vice versa.
        spsel = (CORE_REGISTER['control'] & 2) >> 1
        if reg == CORE_REGISTER['sp']:
            if spsel:
                self._regs[CORE_REGISTER['psp']] = value
            else:
                self._regs[CORE_REGISTER['msp']] = value
        elif (reg == CORE_REGISTER['msp'] and spsel == 0) or \
                (reg == CORE_REGISTER['psp'] and spsel == 1):
            self._regs[CORE_REGISTER['sp']] = value

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

    def write_memory_block(self, addr, data):
        mem, offset = self._find_mem(addr)
        if mem:
            mem.data[offset:offset+len(data)] = data

    def read_memory_block(self, addr, length):
        mem, offset = self._find_mem(addr)
        if mem:
            return bytearray(mem.data[offset:offset+length])


