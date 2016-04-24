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

from ..bitstring import *
from ..disasm import decoder
from ..model import CpuModel
from ..mock_cpu import MockCpuModelDelegate
from ..utilities import (le16_to_bytes, le32_to_bytes)
from ..formatter import Formatter
import pytest

@pytest.fixture(scope='function')
def cpu():
    c = CpuModel()
    c.delegate = MockCpuModelDelegate()
    c.pc = 0x8000
    c.sp = 0x20004000
    return c

@pytest.fixture(scope='function')
def fmt(cpu):
    return Formatter(cpu)

class TestAdd:
    def test_add_sp_pl_imm_t1(self, cpu, fmt):
        i = decoder.decode(le16_to_bytes(0b1010100100000101)) # add r1, sp, #20
        assert i.d == 1
        assert i.imm32 == 20
        print fmt.format(i)
        sp = cpu.sp.unsigned
        r1 = cpu.r[1].unsigned
        i.execute(cpu)
        assert cpu.r[1] == sp + 20

    def test_add_sp_pl_imm_t2(self, cpu, fmt):
        i = decoder.decode(le16_to_bytes(0b1011000000001000)) # add sp, sp, #32
        assert i.d == 13
        assert i.imm32 == 32
        print fmt.format(i)
        sp = cpu.sp.unsigned
        i.execute(cpu)
        assert cpu.sp == sp + 32

    def test_add_reg_t1(self, cpu, fmt):
        cpu.r[2] = bitstring(150)
        cpu.r[3] = bitstring(1000)
        i = decoder.decode(le16_to_bytes(0b0001100011010001)) # add r1, r2, r3
        assert i.m == 3
        assert i.n == 2
        assert i.d == 1
        print fmt.format(i)
        i.execute(cpu)
        assert cpu.r[1] == 1150

    def test_add_reg_t2_r3(self, cpu, fmt):
        cpu.r[2] = bitstring(150)
        cpu.r[3] = bitstring(1000)
        i = decoder.decode(le16_to_bytes(0b0100010000011010)) # add r2, r3
        assert i.m == 3
        assert i.n == 2
        assert i.d == 2
        print fmt.format(i)
        i.execute(cpu)
        assert cpu.r[2] == 1150

    def test_add_reg_t2_pc(self, cpu, fmt):
        cpu.r[2] = bitstring(1150)
        i = decoder.decode(le16_to_bytes(0b0100010001111010)) # add r2, pc
        assert i.m == 15
        assert i.n == 2
        assert i.d == 2
        print fmt.format(i)
        pc = cpu.pc.unsigned
        i.execute(cpu)
        assert cpu.r[2] == pc + 1150

    def test_add_imm_t1(self, cpu, fmt):
        cpu.r[2] = bitstring(200)
        i = decoder.decode(le16_to_bytes(0b0001110011010001)) # adds r1, r2, #3
        assert i.n == 2
        assert i.d == 1
        print fmt.format(i)
        i.execute(cpu)
        assert cpu.r[1] == 203

    def test_add_imm_t2(self, cpu, fmt):
        cpu.r[1] = bitstring(100)
        i = decoder.decode(le16_to_bytes(0b0011000101000100)) # adds r1, #68
        assert i.n == 1
        assert i.d == 1
        print fmt.format(i)
        i.execute(cpu)
        assert cpu.r[1] == 168

    def test_adc_t1_nocarry(self, cpu, fmt):
        cpu.apsr.c = 0
        cpu.r[7] = bitstring(2)
        cpu.r[3] = bitstring(1)
        i = decoder.decode(le16_to_bytes(0b0100000101111011)) # adcs r3, r7
        assert i.m == 7
        assert i.n == 3
        assert i.d == 3
        print fmt.format(i)
        i.execute(cpu)
        assert cpu.r[3] == 3

    def test_adc_t1_carry(self, cpu, fmt):
        cpu.apsr.c = 1
        cpu.r[7] = bitstring(2)
        cpu.r[3] = bitstring(1)
        i = decoder.decode(le16_to_bytes(0b0100000101111011)) # adcs r3, r7
        assert i.m == 7
        assert i.n == 3
        assert i.d == 3
        print fmt.format(i)
        i.execute(cpu)
        assert cpu.r[3] == 4

class TestBranch:
    def test_b_t1_eq_pos(self, cpu, fmt):
        for z in (0, 1):
            cpu.apsr.z = z
            i = decoder.decode(le16_to_bytes(0b1101000000011000)) # beq .+48
            assert i.imm32 == 48
            print fmt.format(i)
            pc = cpu.pc.unsigned
            i.execute(cpu)
            if z:
                assert cpu.pc == pc + 4 + 48
            else:
                assert cpu.pc == pc + 2

    def test_b_t1_cc_neg(self, cpu, fmt):
        for c in (0, 1):
            cpu.apsr.c = c
            i = decoder.decode(le16_to_bytes(0b1101001111111100)) # bcc .-48
            print fmt.format(i)
            assert i.imm32.signed == -8
            pc = cpu.pc.unsigned
            i.execute(cpu)
            if c:
                assert cpu.pc == pc + 2
            else:
                assert cpu.pc == pc + 4 - 8

    def test_bl_t1(self, cpu, fmt):
        i = decoder.decode(bytearray([0x01, 0xf0, 0xaf, 0xff])) # bl .+0x1f5e
        print fmt.format(i)
        assert i.imm32.signed == 0x1f5e
        pc = cpu.pc.unsigned
        i.execute(cpu)
        assert cpu.lr == (pc + 4) | 1  # set T bit
        assert cpu.pc == pc + 4 + 0x1f5e

    def test_blx_t1(self, cpu, fmt):
        cpu.r[3] = 0x1001
        i = decoder.decode(le16_to_bytes(0b0100011110011000)) # blx r3
        print fmt.format(i)
        assert i.m == 3
        pc = cpu.pc.unsigned
        i.execute(cpu)
        assert cpu.lr == (pc + 2) | 1  # set T bit
        assert cpu.pc == cpu.r[3] & ~1




