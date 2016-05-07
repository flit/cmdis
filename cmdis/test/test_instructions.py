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
from ..bitstring import *
from ..disasm import decoder
from ..model import CpuModel
from ..mock_cpu import MockCpuModelDelegate
from ..utilities import (le16_to_bytes, le32_to_bytes)
from ..formatter import Formatter
from ..registers import CORE_REGISTER
import pytest
import string
import six

##
# @brief Utility to evaluate instruction format strings.
#
# The
def format_bits(bits, **kwargs):
    i = 0
    state = 0
    result = ''
    ident = ''
    width = ''
    while i < len(bits):
        c = bits[i]
        i += 1
        if state == 0:
            if c == '{':
                state = 1
                ident = ''
                width = ''
            elif c in ('0', '1', ','):
                result += c
            elif c in string.ascii_letters:
                state = 3
            else:
                pass
        elif state == 1:
            if c in string.ascii_letters + string.digits:
                ident += c
            elif c == ':':
                state = 2
            elif c == '}':
                value = bitstring(kwargs[ident], 1)
                result += value.binary_string
                state = 0
            else:
                raise ValueError("unexpected character '%s'" % c)
        elif state == 2:
            if c in string.digits:
                width += c
            elif c == '}':
                value = bitstring(kwargs[ident], int(width))
                result += value.binary_string
                state = 0
            else:
                raise ValueError("unexpected character '%s'" % c)
        elif state == 3:
            # Ignore everything until the '='
            if c == '=':
                state = 0

    return result

def fmt_16bit(bits, **kwargs):
    bits = format_bits(bits, **kwargs)
    hw1 = bitstring(bits)
    return hw1.bytes

def fmt_32bit(bits, **kwargs):
    bits = format_bits(bits, **kwargs)
    hw1, hw2 = bits.split(',')
    hw1 = bitstring(hw1)
    hw2 = bitstring(hw2)
    return hw1.bytes + hw2.bytes

@pytest.fixture(scope='function')
def cpu():
    c = CpuModel()
    c.delegate = MockCpuModelDelegate()
    c.delegate.add_memory(0, 0x10000)
    c.delegate.add_memory(0x20000000, 0x8000)
    c.pc = 0x8000
    c.sp = 0x20004000
    return c

@pytest.fixture(scope='function')
def fmt(cpu):
    return Formatter(cpu)

@pytest.fixture(params=range(8))
def reg3bit(request):
    return request.param

@pytest.fixture(params=range(8))
def reg3bit2(request):
    return request.param

@pytest.fixture(params=range(8))
def reg3bit3(request):
    return request.param

@pytest.fixture(params=range(16))
def reg4bit(request):
    return request.param

@pytest.fixture(params=range(15))
def reg4bit_nopc(request):
    return request.param

@pytest.fixture(params=(range(13)+[14,15]))
def reg4bit_nosp(request):
    return request.param

@pytest.fixture(params=(range(13)+[14]))
def reg4bit_nopc_nosp(request):
    return request.param

@pytest.fixture(params=range(1, 1<<8))
def reglist8(request):
    return request.param

@pytest.fixture(params=range(1, 1<<13))
def reglist13(request):
    return request.param

class TestAdd:
    # add r1, sp, #20
    def test_add_sp_pl_imm_t1(self, cpu, fmt):
        i = decoder.decode(le16_to_bytes(0b1010100100000101))
        assert i.d == 1
        assert i.imm32 == 20
        print(fmt.format(i))
        sp = cpu.sp.unsigned
        r1 = cpu.r[1].unsigned
        i.execute(cpu)
        assert cpu.r[1] == sp + 20

    # add sp, sp, #32
    def test_add_sp_pl_imm_t2(self, cpu, fmt):
        i = decoder.decode(le16_to_bytes(0b1011000000001000))
        assert i.d == 13
        assert i.imm32 == 32
        print(fmt.format(i))
        sp = cpu.sp.unsigned
        i.execute(cpu)
        assert cpu.sp == sp + 32

    # add rD, sp, rM
    @pytest.mark.parametrize("Rdm", [2, 11])
    def test_add_sp_pl_reg_t1(self, cpu, fmt, Rdm):
        cpu.r[Rdm] = 200
        i = decoder.decode(fmt_16bit("01000100 {DM} 1101 {Rdm:3}", DM=((Rdm >> 3) & 1), Rdm=Rdm))
        assert i.m == Rdm
        assert i.n == 13
        assert i.d == Rdm
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rdm] == cpu.sp + 200

    # add sp, rM
    @pytest.mark.parametrize("Rm", [2, 11])
    def test_add_sp_pl_reg_t2(self, cpu, fmt, Rm):
        cpu.r[Rm] = 200
        i = decoder.decode(fmt_16bit("01000100 1 {Rm:4} 101", Rm=Rm))
        assert i.m == Rm
        assert i.n == 13
        assert i.d == 13
        print(fmt.format(i))
        sp = cpu.sp
        i.execute(cpu)
        assert cpu.sp == sp + 200

    # add r1, r2, r3
    def test_add_reg_t1(self, cpu, fmt):
        cpu.r[2] = bitstring(150)
        cpu.r[3] = bitstring(1000)
        i = decoder.decode(le16_to_bytes(0b0001100011010001))
        assert i.m == 3
        assert i.n == 2
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 1150

    # add r2, r3
    def test_add_reg_t2_r3(self, cpu, fmt):
        cpu.r[2] = bitstring(150)
        cpu.r[3] = bitstring(1000)
        i = decoder.decode(le16_to_bytes(0b0100010000011010))
        assert i.m == 3
        assert i.n == 2
        assert i.d == 2
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[2] == 1150

    # add r2, pc
    def test_add_reg_t2_pc(self, cpu, fmt):
        cpu.r[2] = bitstring(1150)
        i = decoder.decode(le16_to_bytes(0b0100010001111010))
        assert i.m == 15
        assert i.n == 2
        assert i.d == 2
        print(fmt.format(i))
        pc = cpu.pc.unsigned
        i.execute(cpu)
        assert cpu.r[2] == pc + 1150

    # adds r1, r2, #3
    def test_add_imm_t1(self, cpu, fmt):
        cpu.r[2] = bitstring(200)
        i = decoder.decode(le16_to_bytes(0b0001110011010001))
        assert i.n == 2
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 203

    # adds r1, #68
    def test_add_imm_t2(self, cpu, fmt):
        cpu.r[1] = bitstring(100)
        i = decoder.decode(le16_to_bytes(0b0011000101000100))
        assert i.n == 1
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 168

    # adcs r3, r7
    @pytest.mark.parametrize("c", [0, 1])
    def test_adc_reg_t1(self, cpu, fmt, c):
        cpu.apsr.c = c
        cpu.r[7] = bitstring(2)
        cpu.r[3] = bitstring(1)
        i = decoder.decode(le16_to_bytes(0b0100000101111011))
        assert i.m == 7
        assert i.n == 3
        assert i.d == 3
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[3] == 3 + c

class TestSub:
    # sub sp, sp, #20
    def test_sub_minus_imm_t1(self, cpu, fmt):
        i = decoder.decode(le16_to_bytes(0b1011000010000101))
        assert i.imm32 == 20
        print(fmt.format(i))
        sp = cpu.sp.unsigned
        i.execute(cpu)
        assert cpu.sp.unsigned == sp - 20

    # sub r1, r3, r2
    def test_sub_reg_t1(self, cpu, fmt):
        cpu.r[2] = bitstring(150)
        cpu.r[3] = bitstring(1000)
        i = decoder.decode(le16_to_bytes(0b0001101010011001))
        assert i.m == 2
        assert i.n == 3
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 850

    # sbcs r1, r3
    # TODO verify this is correct behaviour
    @pytest.mark.parametrize("c", [0, 1])
    def test_sbc_reg_t1(self, cpu, fmt, c):
        cpu.apsr.c = c
        cpu.r[3] = bitstring(150)
        cpu.r[1] = bitstring(1000)
        i = decoder.decode(le16_to_bytes(0b0100000110011001))
        assert i.m == 3
        assert i.n == 1
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 850 - ((1, 0)[c])

    # subs r1, r2, #3
    def test_sub_imm_t1(self, cpu, fmt):
        cpu.r[2] = bitstring(200)
        i = decoder.decode(le16_to_bytes(0b0001111011010001))
        assert i.n == 2
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 197

    # subs r2, #127
    def test_sub_imm_t2(self, cpu, fmt):
        cpu.r[2] = bitstring(200)
        i = decoder.decode(le16_to_bytes(0b0011101001111111))
        assert i.n == 2
        assert i.d == 2
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[2] == 73

class TestReverseSubtract:
    # rsbs r1, r2, #0
    def test_rsb_t1(self, cpu, fmt):
        Rn = 2
        Rd = 1
        cpu.r[Rn] = bitstring(200)
        cpu.r[Rd] = bitstring(100)
        i = decoder.decode(fmt_16bit("010000 1001 {Rn:3} {Rd:3}", Rn=Rn, Rd=Rd))
        assert i.n == Rn
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == 0 - 200

    # rsb{s}.w r1, r2, #212
    @pytest.mark.parametrize("S", [0, 1])
    def test_rsb_t2(self, cpu, fmt, S):
        Rn = 2
        Rd = 1
        cpu.r[Rn] = bitstring(200)
        cpu.r[Rd] = bitstring(100)
        im, imm3, imm8 = 0, 0, 212
        i = decoder.decode(fmt_32bit("11110 {im} 0 1110 {S} {Rn:4}, 0 {imm3:3} {Rd:4} {imm8:8}", im=im, S=S, imm3=imm3, imm8=imm8, Rn=Rn, Rd=Rd))
        assert i.n == Rn
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == 212 - 200

class TestMultiply:
    # muls r1, r2, r1
    def test_mul_t1(self, cpu, fmt):
        Rdm = 1
        Rn = 2
        cpu.r[Rdm] = bitstring(0x0c1)
        cpu.r[Rn] = bitstring(0x180)
        i = decoder.decode(fmt_16bit("010000 1101 {Rn:3} {Rdm:3}", Rn=Rn, Rdm=Rdm))
        assert i.m == Rdm
        assert i.n == Rn
        assert i.d == Rdm
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rdm] == (0x0c1 * 0x180)

    # mul r1, r2, r12
    def test_mul_t2(self, cpu, fmt):
        Rm = 12
        Rn = 2
        Rd = 1
        cpu.r[Rm] = bitstring(0x0c1)
        cpu.r[Rn] = bitstring(0x180)
        i = decoder.decode(fmt_32bit("11111 0110 000 {Rn:4}, 1111 {Rd:4} 0000 {Rm:4}", Rn=Rn, Rd=Rd, Rm=Rm))
        assert i.m == Rm
        assert i.n == Rn
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == (0x0c1 * 0x180)

class TestBitOps:
    # ands r1, r4
    def test_and_reg_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x0c1)
        cpu.r[1] = bitstring(0x180)
        i = decoder.decode(le16_to_bytes(0b0100000000100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x080

    # eors r1, r4
    def test_eor_reg_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x0c1)
        cpu.r[1] = bitstring(0x180)
        i = decoder.decode(le16_to_bytes(0b0100000001100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x141

    # orrs r1, r4
    def test_orr_reg_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x0c1)
        cpu.r[1] = bitstring(0x180)
        i = decoder.decode(le16_to_bytes(0b0100001100100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x1c1

    # bics r1, r4
    def test_bic_reg_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x080)
        cpu.r[1] = bitstring(0x180)
        i = decoder.decode(le16_to_bytes(0b0100001110100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x100

class TestShifts:
    # rors r1, r4
    def test_ror_reg_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x108)
        cpu.r[1] = bitstring(0x7e)
        i = decoder.decode(le16_to_bytes(0b0100000111100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x7e000000

    # asrs r1, r4
    @pytest.mark.parametrize(("r1", "expected"), [
        (0x7e00, 0x7e),
        (0xffff7e00, 0xffffff7e),
        ])
    def test_asr_reg_t1(self, cpu, fmt, r1, expected):
        cpu.r[4] = bitstring(0x108)
        cpu.r[1] = bitstring(r1)
        i = decoder.decode(le16_to_bytes(0b0100000100100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == expected

    # lsrs r1, r4
    @pytest.mark.parametrize(("r1", "expected"), [
        (0x7e00, 0x7e),
        (0xffff7e00, 0x00ffff7e),
        ])
    def test_lsr_reg_t1(self, cpu, fmt, r1, expected):
        cpu.r[4] = bitstring(0x108)
        cpu.r[1] = bitstring(r1)
        i = decoder.decode(le16_to_bytes(0b0100000011100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == expected

    # lsls r1, r4
    def test_lsl_reg_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x108)
        cpu.r[1] = bitstring(0x7e)
        i = decoder.decode(le16_to_bytes(0b0100000010100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x7e00

    # lsls r1, r4, #3
    def test_lsl_imm_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x108)
        i = decoder.decode(le16_to_bytes(0b0000000011100001))
        assert i.n == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x840

    # lsrs r1, r4, #3
    def test_lsr_imm_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x108)
        i = decoder.decode(le16_to_bytes(0b0000100011100001))
        assert i.n == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x21

    # asrs r1, r4, #3
    @pytest.mark.parametrize(("r4", "expected"), [
        (0x7e00, 0xfc0),
        (0xffff7e00, 0xffffefc0),
        ])
    def test_asr_imm_t1(self, cpu, fmt, r4, expected):
        cpu.r[4] = bitstring(r4)
        i = decoder.decode(le16_to_bytes(0b0001000011100001))
        assert i.n == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == expected

class TestByteReverse:
    # rev r1, r2
    @pytest.mark.parametrize(("v", "e"), [
        (0x12345678, 0x78563412),
        ])
    def test_rev_t1(self, cpu, fmt, v, e):
        Rm = 2
        Rd = 1
        cpu.r[Rm] = bitstring(v)
        i = decoder.decode(fmt_16bit('1011 1010 00 {Rm:3} {Rd:3}', Rm=Rm, Rd=Rd))
        assert i.m == Rm
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == e

    # rev.w r1, r12
    @pytest.mark.parametrize(("v", "e"), [
        (0x12345678, 0x78563412),
        ])
    def test_rev_t2(self, cpu, fmt, v, e):
        Rm = 12
        Rd = 1
        cpu.r[Rm] = bitstring(v)
        i = decoder.decode(fmt_32bit('11111 010 1 001 {Rm1:4}, 1111 {Rd:4} 1 000 {Rm2:4}', Rm1=Rm, Rm2=Rm, Rd=Rd))
        assert i.m == Rm
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == e

    # rev16 r1, r2
    @pytest.mark.parametrize(("v", "e"), [
        (0x12345678, 0x34127856),
        ])
    def test_rev16_t1(self, cpu, fmt, v, e):
        Rm = 2
        Rd = 1
        cpu.r[Rm] = bitstring(v)
        i = decoder.decode(fmt_16bit('1011 1010 01 {Rm:3} {Rd:3}', Rm=Rm, Rd=Rd))
        assert i.m == Rm
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == e

    # rev16.w r1, r12
    @pytest.mark.parametrize(("v", "e"), [
        (0x12345678, 0x34127856),
        ])
    def test_rev16_t2(self, cpu, fmt, v, e):
        Rm = 12
        Rd = 1
        cpu.r[Rm] = bitstring(v)
        i = decoder.decode(fmt_32bit('11111 010 1 001 {Rm1:4}, 1111 {Rd:4} 1 001 {Rm2:4}', Rm1=Rm, Rm2=Rm, Rd=Rd))
        assert i.m == Rm
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == e

    # revsh r1, r2
    @pytest.mark.parametrize(("v", "e"), [
        (0x12345678, 0x00007856),
        (0x000056f8, 0xfffff856),
        ])
    def test_revsh_t1(self, cpu, fmt, v, e):
        Rm = 2
        Rd = 1
        cpu.r[Rm] = bitstring(v)
        i = decoder.decode(fmt_16bit('1011 1010 11 {Rm:3} {Rd:3}', Rm=Rm, Rd=Rd))
        assert i.m == Rm
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == e

    # revsh.w r1, r12
    @pytest.mark.parametrize(("v", "e"), [
        (0x12345678, 0x00007856),
        (0x000056f8, 0xfffff856),
        ])
    def test_revsh_t2(self, cpu, fmt, v, e):
        Rm = 12
        Rd = 1
        cpu.r[Rm] = bitstring(v)
        i = decoder.decode(fmt_32bit('11111 010 1 001 {Rm1:4}, 1111 {Rd:4} 1 011 {Rm2:4}', Rm1=Rm, Rm2=Rm, Rd=Rd))
        assert i.m == Rm
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == e

class TestAdr:
    # adr r3, label
    def test_adr_t1(self, cpu, fmt):
        Rd = 3
        imm = 28
        i = decoder.decode(fmt_16bit('1010 0 {Rd:3} {imm:8}', Rd=Rd, imm=imm>>2))
        assert i.d == Rd
        print(fmt.format(i))
        pc = cpu.pc.unsigned
        i.execute(cpu)
        assert cpu.r[Rd] == pc + 4 + imm

    # adr.w r3, label
    @pytest.mark.parametrize(("Rd", "imm"), [
        (3, 28),
        (12, 3060),
        ])
    def test_adr_t2(self, cpu, fmt, Rd, imm):
        imm_bits = bitstring(imm)
        i = decoder.decode(fmt_32bit('11110 {im} 10101 0 1111, 0 {imm3:3} {Rd:4} {imm8:8}',
            Rd=Rd, im=imm_bits[11], imm3=imm_bits[8:11], imm8=imm_bits[0:8]))
        assert i.d == Rd
        print(fmt.format(i))
        pc = cpu.pc.unsigned
        i.execute(cpu)
        assert cpu.r[Rd] == pc + 4 - imm

    # adr.w r3, label
    @pytest.mark.parametrize(("Rd", "imm"), [
        (3, 28),
        (12, 3060),
        ])
    def test_adr_t3(self, cpu, fmt, Rd, imm):
        imm_bits = bitstring(imm)
        i = decoder.decode(fmt_32bit('11110 {im} 10000 0 1111, 0 {imm3:3} {Rd:4} {imm8:8}',
            Rd=Rd, im=imm_bits[11], imm3=imm_bits[8:11], imm8=imm_bits[0:8]))
        assert i.d == Rd
        print(fmt.format(i))
        pc = cpu.pc.unsigned
        i.execute(cpu)
        assert cpu.r[Rd] == pc + 4 + imm

class TestExtend:
    # uxtb r1, r4
    def test_uxtb_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x108)
        i = decoder.decode(le16_to_bytes(0b1011001011100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x08

    # uxtb.w r1, r11, ROR #24
    def test_uxtb_t2(self, cpu, fmt):
        cpu.r[11] = bitstring(0xa7002011)
        i = decoder.decode(le16_to_bytes(0b1111101001011111)+le16_to_bytes(0b1111000110111011))
        assert i.m == 11
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0xa7

    # uxth r1, r4
    def test_uxth_t1(self, cpu, fmt):
        cpu.r[4] = bitstring(0x77108)
        i = decoder.decode(le16_to_bytes(0b1011001010100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x7108

    # uxth.w r1, r11, ROR #8
    def test_uxth_t2(self, cpu, fmt):
        cpu.r[11] = bitstring(0xa7002011)
        i = decoder.decode(le16_to_bytes(0b1111101000011111)+le16_to_bytes(0b1111000110011011))
        assert i.m == 11
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == 0x0020

    # sxtb r1, r4
    @pytest.mark.parametrize(("r4", "expected"), [
        (0x7e20, 0x20),
        (0xfe, 0xfffffffe),
        ])
    def test_sxtb_t1(self, cpu, fmt, r4, expected):
        cpu.r[4] = bitstring(r4)
        i = decoder.decode(le16_to_bytes(0b1011001001100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == expected

    # sxtb.w r1, r11, ROR #8
    @pytest.mark.parametrize(("r4", "expected"), [
        (0x7e20, 0x7e),
        (0xfe12, 0xfffffffe),
        (0x10fe12, 0xfffffffe),
        ])
    def test_sxtb_t2(self, cpu, fmt, r4, expected):
        cpu.r[11] = bitstring(r4)
        i = decoder.decode(le16_to_bytes(0b1111101001001111)+le16_to_bytes(0b1111000110011011))
        assert i.m == 11
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == expected

    # sxth r1, r4
    @pytest.mark.parametrize(("r4", "expected"), [
        (0x117e20, 0x7e20),
        (0xffae, 0xffffffae),
        (0x18ffae, 0xffffffae),
        ])
    def test_sxth_t1(self, cpu, fmt, r4, expected):
        cpu.r[4] = bitstring(r4)
        i = decoder.decode(le16_to_bytes(0b1011001000100001))
        assert i.m == 4
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == expected

    # sxth.w r1, r11, ROR #8
    @pytest.mark.parametrize(("r4", "expected"), [
        (0x197e20, 0x197e),
        (0xfebe12, 0xfffffebe),
        (0x10febe12, 0xfffffebe),
        ])
    def test_sxth_t2(self, cpu, fmt, r4, expected):
        cpu.r[11] = bitstring(r4)
        i = decoder.decode(le16_to_bytes(0b1111101000001111)+le16_to_bytes(0b1111000110011011))
        assert i.m == 11
        assert i.d == 1
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[1] == expected

class TestMove:
    # movs r3, #7
    def test_mov_imm_t1(self, cpu, fmt):
        i = decoder.decode(le16_to_bytes(0b0010001100000111))
        assert i.imm32 == 7
        assert i.d == 3
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[3] == 7

    # movs r3, r7
    def test_mov_reg_t2(self, cpu, fmt):
        cpu.r[7] = bitstring(0x1234)
        i = decoder.decode(le16_to_bytes(0b0000000000111011))
        assert i.m == 7
        assert i.d == 3
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[3] == 0x1234

    # movs r0, r0
    def test_mov_reg_t2(self, cpu, fmt):
        cpu.r[0] = bitstring(0x1234)
        i = decoder.decode(le16_to_bytes(0b0000000000000000))
        assert i.m == 0
        assert i.d == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == 0x1234

    # mov r2, r12
    def test_mov_reg_t1_0(self, cpu, fmt):
        cpu.r[12] = bitstring(0x1234)
        i = decoder.decode(le16_to_bytes(0b0100011001100010))
        assert i.m == 12
        assert i.d == 2
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[2] == 0x1234

    # mov r12, r2
    def test_mov_reg_t1_1(self, cpu, fmt):
        cpu.r[2] = bitstring(0x1234)
        i = decoder.decode(le16_to_bytes(0b0100011010010100))
        assert i.m == 2
        assert i.d == 12
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[12] == 0x1234

    # mov{s}.w r12, r2
    @pytest.mark.parametrize("S", [0, 1])
    def test_mov_reg_t3_1(self, cpu, fmt, S):
        cpu.r[2] = bitstring(0x1234)
        i = decoder.decode(fmt_32bit('11101010010{S}1111,0000110000000010', S=S))
        assert i.m == 2
        assert i.d == 12
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[12] == 0x1234

    # mvns r1, r7
    @pytest.mark.parametrize(("v", "e"), [
            (0, 0xffffffff),
            (0xffffffff, 0),
        ])
    def test_mvn_reg_t1(self, cpu, fmt, v, e):
        Rd = 1
        Rm = 7
        cpu.r[Rm] = v
        i = decoder.decode(fmt_16bit('010000 1111 {Rm:3} {Rd:3}', Rm=Rm, Rd=Rd))
        assert i.m == Rm
        assert i.d == Rd
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rd] == e

class TestCompare:
    # cmp r3, #7
    def test_mov_t1(self, cpu, fmt):
        cpu.r[3] = 7
        i = decoder.decode(le16_to_bytes(0b0010101100000111))
        assert i.imm32 == 7
        assert i.n == 3
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.apsr.z == 1
        assert cpu.apsr.n == 0

class TestTest:
    # tst r3, r7
    @pytest.mark.parametrize(("nv", "mv", "n", "z", "c"), [
            (0, 0, 0, 1, 0),
            (0, 1, 0, 1, 0),
            (1, 1, 0, 0, 0),
            (0xffffffff, 0xffffffff, 1, 0, 0),
        ])
    def test_tst_t1(self, cpu, fmt, nv, mv, n, z, c):
        Rm = 7
        Rn = 3
        cpu.r[Rn] = bitstring(nv)
        cpu.r[Rm] = bitstring(mv)
        i = decoder.decode(fmt_16bit('010000 1000 {Rm:3} {Rn:3}', Rm=Rm, Rn=Rn))
        assert i.m == Rm
        assert i.n == Rn
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.apsr.n == n
        assert cpu.apsr.z == z
        assert cpu.apsr.c == c

    # tst.w r3, r7
    @pytest.mark.parametrize(("nv", "mv", "type", "shft", "n", "z", "c"), [
            (0, 0, 0, 0, 0, 1, 0),
            (0, 1, 0, 0, 0, 1, 0),
            (1, 1, 0, 0, 0, 0, 0),
            (8, 1, 0, 3, 0, 0, 0),
            (1, 8, 1, 3, 0, 0, 0),
            (0xffffffff, 0xffffffff, 0, 0, 1, 0, 0),
        ])
    def test_tst_t2(self, cpu, fmt, nv, mv, type, shft, n, z, c):
        Rm = 7
        Rn = 3
        imm3, imm2 = bitstring(shft)[2:5], bitstring(shft)[0:2]
        cpu.r[Rn] = bitstring(nv)
        cpu.r[Rm] = bitstring(mv)
        i = decoder.decode(fmt_32bit('11101 01 0000 1 {Rn:4}, 0 {imm3:3} 1111 {imm2:2} {type:2} {Rm:4}', Rm=Rm, Rn=Rn, imm3=imm3, imm2=imm2, type=type))
        assert i.m == Rm
        assert i.n == Rn
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.apsr.n == n
        assert cpu.apsr.z == z
        assert cpu.apsr.c == c

class TestBranch:
    # beq .+48
    @pytest.mark.parametrize("z", [0, 1])
    def test_b_t1_eq_pos(self, cpu, fmt, z):
        cpu.apsr.z = z
        i = decoder.decode(le16_to_bytes(0b1101000000011000))
        assert i.imm32 == 48
        print(fmt.format(i))
        pc = cpu.pc.unsigned
        i.execute(cpu)
        if z:
            assert cpu.pc == pc + 4 + 48
        else:
            assert cpu.pc == pc + 2

    # bcc .-48
    @pytest.mark.parametrize("c", [0, 1])
    def test_b_t1_cc_neg(self, cpu, fmt, c):
        cpu.apsr.c = c
        i = decoder.decode(le16_to_bytes(0b1101001111111100))
        print(fmt.format(i))
        assert i.imm32.signed == -8
        pc = cpu.pc.unsigned
        i.execute(cpu)
        if c:
            assert cpu.pc == pc + 2
        else:
            assert cpu.pc == pc + 4 - 8

    # bl .+0x1f5e
    def test_bl_t1(self, cpu, fmt):
        i = decoder.decode(bytearray([0x01, 0xf0, 0xaf, 0xff]))
        print(fmt.format(i))
        assert i.imm32.signed == 0x1f5e
        pc = cpu.pc.unsigned
        i.execute(cpu)
        assert cpu.lr == (pc + 4) | 1  # set T bit
        assert cpu.pc == pc + 4 + 0x1f5e

    # blx r3
    def test_blx_t1(self, cpu, fmt):
        cpu.r[3] = 0x1001
        i = decoder.decode(le16_to_bytes(0b0100011110011000))
        print(fmt.format(i))
        assert i.m == 3
        pc = cpu.pc.unsigned
        i.execute(cpu)
        assert cpu.lr == (pc + 2) | 1  # set T bit
        assert cpu.pc == cpu.r[3] & ~1

    # bx r3
    def test_bx_t1(self, cpu, fmt):
        cpu.r[3] = 0x1001
        i = decoder.decode(le16_to_bytes(0b0100011100011000))
        print(fmt.format(i))
        assert i.m == 3
        pc = cpu.pc.unsigned
        lr = cpu.lr
        i.execute(cpu)
        assert cpu.lr == lr
        assert cpu.pc == cpu.r[3] & ~1

class TestLoad:
    # ldr r0, [r1, r2]
    def test_ldr(self, cpu, fmt):
        cpu.write32(0x1128, 0x12345678)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1000
        cpu.r[2] = 0x128
        i = decoder.decode(fmt_16bit('0101 100 Rm=010 Rn=001 Rt=000'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == 0x12345678

    # ldrh r0, [r1, r2]
    def test_ldrh(self, cpu, fmt):
        cpu.write16(0x1128, 0x1234)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1000
        cpu.r[2] = 0x128
        i = decoder.decode(fmt_16bit('0101 101 Rm=010 Rn=001 Rt=000'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == 0x00001234

    # ldrsh r0, [r1, r2]
    @pytest.mark.parametrize(("v", "e"), [
            (0x1234, 0x00001234),
            (0xff68, 0xffffff68),
        ])
    def test_ldrsh(self, cpu, fmt, v, e):
        cpu.write16(0x1128, v)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1000
        cpu.r[2] = 0x128
        i = decoder.decode(fmt_16bit('0101 111 Rm=010 Rn=001 Rt=000'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == e

    # ldrb r0, [r1, r2]
    def test_ldrb(self, cpu, fmt):
        cpu.write8(0x1129, 0x77)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1000
        cpu.r[2] = 0x129
        i = decoder.decode(fmt_16bit('0101 110 Rm=010 Rn=001 Rt=000'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == 0x00000077

    # ldrsb r0, [r1, r2]
    @pytest.mark.parametrize(("v", "e"), [
            (0x12, 0x00000012),
            (0xf6, 0xfffffff6),
        ])
    def test_ldrsb(self, cpu, fmt, v, e):
        cpu.write8(0x1129, v)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1000
        cpu.r[2] = 0x129
        i = decoder.decode(fmt_16bit('0101 011 Rm=010 Rn=001 Rt=000'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == e

    # ldr.w r0, [r1, r2, LSL #1]
    def test_ldr_w(self, cpu, fmt):
        cpu.write32(0x1008, 0x12345678)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1000
        cpu.r[2] = 4
        i = decoder.decode(fmt_32bit('11111 00 0 0 10 1 Rn=0001, Rt=0000 0 00000 imm2=01 Rm=0010'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == 0x12345678

    # ldrh.w r0, [r1, r2, LSL #1]
    def test_ldrh_w(self, cpu, fmt):
        cpu.write16(0x100a, 0x1234)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1002
        cpu.r[2] = 4
        i = decoder.decode(fmt_32bit('11111 00 0 0 01 1 Rn=0001, Rt=0000 0 00000 imm2=01 Rm=0010'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == 0x00001234

    # ldrsh.w r0, [r1, r2, LSL #1]
    @pytest.mark.parametrize(("v", "e"), [
            (0x1234, 0x00001234),
            (0xff68, 0xffffff68),
        ])
    def test_ldrsh_w(self, cpu, fmt, v, e):
        cpu.write16(0x100a, v)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1002
        cpu.r[2] = 4
        i = decoder.decode(fmt_32bit('11111 00 1 0 01 1 Rn=0001, Rt=0000 0 00000 imm2=01 Rm=0010'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == e

    # ldrb.w r0, [r1, r2, LSL #1]
    def test_ldrb_w(self, cpu, fmt):
        cpu.write8(0x1009, 0x77)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1001
        cpu.r[2] = 4
        i = decoder.decode(fmt_32bit('11111 00 0 0 00 1 Rn=0001, Rt=0000 0 00000 imm2=01 Rm=0010'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == 0x00000077

    # ldrsb.w r0, [r1, r2, LSL #1]
    @pytest.mark.parametrize(("v", "e"), [
            (0x12, 0x00000012),
            (0xf6, 0xfffffff6),
        ])
    def test_ldrsb_w(self, cpu, fmt, v, e):
        cpu.write8(0x1009, v)
        cpu.r[0] = 0xa5a5a5a5
        cpu.r[1] = 0x1001
        cpu.r[2] = 4
        i = decoder.decode(fmt_32bit('11111 00 1 0 00 1 Rn=0001, Rt=0000 0 00000 imm2=01 Rm=0010'))
        assert i.m == 2
        assert i.n == 1
        assert i.t == 0
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[0] == e

    # ldr r3, [pc, #8]
    def test_ldr_literal(self, cpu, fmt):
        cpu.write32(0x800c, 0x12345678) # write literal to pc + offset
        cpu.r[3] = 0xa5a5a5a5
        i = decoder.decode(fmt_16bit('01001 Rt=011 imm8=00000010'))
        assert i.t == 3
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[3] == 0x12345678

    # ldr.w r3, [pc, #x]
    @pytest.mark.parametrize(("U", "imm12", "addr"), [
            (1, 4, 0x8008),  # ldr.w r3, [pc, #4]
            (0, 16, 0x7ff4), # ldr.w r3, [pc, #-16]
        ])
    def test_ldr_literal_w(self, cpu, fmt, U, imm12, addr, reg4bit_nopc):
        cpu.write32(addr, 0x12345678) # write literal to pc + offset
        cpu.r[reg4bit_nopc] = 0xa5a5a5a5
        i = decoder.decode(fmt_32bit('11111 00 0 {U} 10 1 1111, {Rt:4} {imm12:12}', U=U, Rt=reg4bit_nopc, imm12=imm12))
        assert i.t == reg4bit_nopc
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[reg4bit_nopc] == 0x12345678

    # ldrh.w r3, [pc, #x]
    @pytest.mark.parametrize(("U", "imm12", "addr"), [
            (1, 4, 0x8008),  # ldrh.w r3, [pc, #4]
            (0, 16, 0x7ff4), # ldrh.w r3, [pc, #-16]
        ])
    def test_ldrh_literal_w(self, cpu, fmt, U, imm12, addr, reg4bit_nopc):
        cpu.write32(addr, 0x12345678) # write literal to pc + offset
        cpu.r[reg4bit_nopc] = 0xa5a5a5a5
        i = decoder.decode(fmt_32bit('11111 00 0 {U} 01 1 1111, {Rt:4} {imm12:12}', U=U, Rt=reg4bit_nopc, imm12=imm12))
        assert i.t == reg4bit_nopc
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[reg4bit_nopc] == 0x5678

    # ldrb.w r3, [pc, #x]
    @pytest.mark.parametrize(("U", "imm12", "addr"), [
            (1, 4, 0x8008),  # ldrb.w r3, [pc, #4]
            (0, 16, 0x7ff4), # ldrb.w r3, [pc, #-16]
        ])
    def test_ldrb_literal_w(self, cpu, fmt, U, imm12, addr, reg4bit_nopc):
        cpu.write32(addr, 0x12345678) # write literal to pc + offset
        cpu.r[reg4bit_nopc] = 0xa5a5a5a5
        i = decoder.decode(fmt_32bit('11111 00 0 {U} 00 1 1111, {Rt:4} {imm12:12}', U=U, Rt=reg4bit_nopc, imm12=imm12))
        assert i.t == reg4bit_nopc
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[reg4bit_nopc] == 0x78

    # ldrsh.w r3, [pc, #x]
    @pytest.mark.parametrize(("U", "imm12", "addr", "v", "e"), [
            (1, 4, 0x8008, 0x1234, 0x00001234),  # ldrsh.w r3, [pc, #4]
            (1, 4, 0x8008, 0xff68, 0xffffff68),  # ldrsh.w r3, [pc, #4]
            (0, 16, 0x7ff4, 0x1234, 0x00001234), # ldrsh.w r3, [pc, #-16]
            (0, 16, 0x7ff4, 0xff68, 0xffffff68), # ldrsh.w r3, [pc, #-16]
        ])
    def test_ldrsh_literal_w(self, cpu, fmt, U, imm12, addr, v, e, reg4bit_nopc):
        cpu.write16(addr, v) # write literal to pc + offset
        cpu.r[reg4bit_nopc] = 0xa5a5a5a5
        i = decoder.decode(fmt_32bit('11111 00 1 {U} 01 1 1111, {Rt:4} {imm12:12}', U=U, Rt=reg4bit_nopc, imm12=imm12))
        assert i.t == reg4bit_nopc
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[reg4bit_nopc] == e

    # ldrsb.w r3, [pc, #x]
    @pytest.mark.parametrize(("U", "imm12", "addr", "v", "e"), [
            (1, 4, 0x8008, 0x14, 0x00000014),  # ldrsb.w r3, [pc, #4]
            (1, 4, 0x8008, 0xf4, 0xfffffff4),  # ldrsb.w r3, [pc, #4]
            (0, 16, 0x7ff4, 0x14, 0x00000014), # ldrsb.w r3, [pc, #-16]
            (0, 16, 0x7ff4, 0xf4, 0xfffffff4), # ldrsb.w r3, [pc, #-16]
        ])
    def test_ldrsb_literal_w(self, cpu, fmt, U, imm12, addr, v, e, reg4bit_nopc):
        cpu.write8(addr, v) # write literal to pc + offset
        cpu.r[reg4bit_nopc] = 0xa5a5a5a5
        i = decoder.decode(fmt_32bit('11111 00 1 {U} 00 1 1111, {Rt:4} {imm12:12}', U=U, Rt=reg4bit_nopc, imm12=imm12))
        assert i.t == reg4bit_nopc
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[reg4bit_nopc] == e

    # ldr r0, [r1, #imm]
    @pytest.mark.parametrize(("addr", "imm",), [
            (0x20000000, 0x0),  # ldr rX, [rY, #0]
            (0x1000, 0x48),  # ldr rX, [rY, #0x48]
            (0x250, 0x7c),  # ldr rX, [rY, #0x7c]
        ])
    def test_ldr_imm_t1(self, cpu, fmt, addr, imm):
        Rn = 1
        Rt = 0
        cpu.write32(addr + imm, 0x12345678)
        cpu.r[Rt] = 0xa5a5a5a5
        cpu.r[Rn] = addr
        i = decoder.decode(fmt_16bit('011 0 1 {imm5:5} {Rn:3} {Rt:3}', imm5=imm>>2, Rn=Rn, Rt=Rt))
        assert i.n == Rn
        assert i.t == Rt
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rt] == 0x12345678

    # ldr r0, [sp, #imm]
    @pytest.mark.parametrize(("addr", "imm",), [
            (0x20000000, 0x0),  # ldr rX, [sp, #0]
            (0x1000, 0x48),  # ldr rX, [sp, #0x48]
            (0x250, 0x7c),  # ldr rX, [sp, #0x7c]
        ])
    def test_ldr_imm_t2(self, cpu, fmt, addr, imm):
        Rt = 0
        cpu.write32(addr + imm, 0x12345678)
        cpu.r[13] = addr
        cpu.r[Rt] = 0xa5a5a5a5
        i = decoder.decode(fmt_16bit('1001 1 {Rt:3} {imm8:8}', imm8=imm>>2, Rt=Rt))
        assert i.t == Rt
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rt] == 0x12345678

    # ldrh r0, [r1, #imm]
    @pytest.mark.parametrize(("addr", "imm",), [
            (0x20000000, 0x0),  # ldrh rX, [rY, #0]
            (0x20000000, 2),  # ldrh rX, [rY, #2]
            (0x1000, 0x18),  # ldrh r0, [r1, #0x18]
            (0x250, 0x38),  # ldrh r0, [r1, #0x38]
        ])
    def test_ldrh_imm_t1(self, cpu, fmt, addr, imm):
        Rn = 1
        Rt = 0
        cpu.write16(addr + imm, 0x5678)
        cpu.r[Rt] = 0xa5a5a5a5
        cpu.r[Rn] = addr
        i = decoder.decode(fmt_16bit('100 0 1 {imm5:5} {Rn:3} {Rt:3}', imm5=imm>>1, Rn=Rn, Rt=Rt))
        assert i.n == Rn
        assert i.t == Rt
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rt] == 0x5678

    # ldrb r0, [r1, #imm]
    @pytest.mark.parametrize(("addr", "imm",), [
            (0x20000000, 0x0),  # ldrb rX, [rY, #0]
            (0x20000000, 1),  # ldrb rX, [rY, #1]
            (0x1000, 28),  # ldrb r0, [r1, #28]
            (0x250, 31),  # ldrb r0, [r1, #31]
        ])
    def test_ldrb_imm_t1(self, cpu, fmt, addr, imm):
        Rn = 1
        Rt = 0
        cpu.write8(addr + imm, 0x78)
        cpu.r[Rt] = 0xa5a5a5a5
        cpu.r[Rn] = addr
        i = decoder.decode(fmt_16bit('011 1 1 {imm5:5} {Rn:3} {Rt:3}', imm5=imm, Rn=Rn, Rt=Rt))
        assert i.n == Rn
        assert i.t == Rt
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[Rt] == 0x78


class TestStore:
    # str r0, [r1, r2]
    def test_str(self, cpu, fmt):
        cpu.r[0] = 0x12341234
        cpu.r[1] = 0x1000
        cpu.r[2] = 0x44
        i = decoder.decode(fmt_16bit('0101 000 Rm=010 Rn=001 Rt=000'))
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read32(0x1044) == 0x12341234

    # strh r0, [r1, r2]
    def test_strh(self, cpu, fmt):
        cpu.r[0] = 0x12345678
        cpu.r[1] = 0x1000
        cpu.r[2] = 0x44
        i = decoder.decode(fmt_16bit('0101 001 Rm=010 Rn=001 Rt=000'))
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read16(0x1042) == 0
        assert cpu.read16(0x1044) == 0x5678
        assert cpu.read16(0x1046) == 0

    # strb r0, [r1, r2]
    def test_strb(self, cpu, fmt):
        cpu.r[0] = 0xaa55
        cpu.r[1] = 0x1000
        cpu.r[2] = 0x45
        i = decoder.decode(fmt_16bit('0101 010 Rm=010 Rn=001 Rt=000'))
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read8(0x1044) == 0
        assert cpu.read8(0x1045) == 0x55
        assert cpu.read8(0x1046) == 0

    # str.w r0, [r1, r2, LSL #1]
    def test_str_w(self, cpu, fmt):
        cpu.r[0] = 0x7788aa55
        cpu.r[1] = 0x1000
        cpu.r[2] = 0x4
        i = decoder.decode(fmt_32bit('11111 00 0 0 10 0 Rn=0001, Rt=0000 0 00000 imm2=01 Rm=0010'))
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read32(0x1008) == 0x7788aa55

    # strh.w r0, [r1, r2, LSL #1]
    def test_strh_w(self, cpu, fmt):
        cpu.r[0] = 0x12345678
        cpu.r[1] = 0x1002
        cpu.r[2] = 0x4
        i = decoder.decode(fmt_32bit('11111 00 0 0 01 0 Rn=0001, Rt=0000 0 00000 imm2=01 Rm=0010'))
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read16(0x1008) == 0
        assert cpu.read16(0x100a) == 0x5678
        assert cpu.read16(0x100c) == 0

    # strb.w r0, [r1, r2, LSL #1]
    def test_strb_w(self, cpu, fmt):
        cpu.r[0] = 0xaa55
        cpu.r[1] = 0x1001
        cpu.r[2] = 0x4
        i = decoder.decode(fmt_32bit('11111 00 0 0 00 0 Rn=0001, Rt=0000 0 00000 imm2=01 Rm=0010'))
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read8(0x1008) == 0
        assert cpu.read8(0x1009) == 0x55
        assert cpu.read8(0x100a) == 0

    # str r0, [r1, #imm]
    @pytest.mark.parametrize(("addr", "imm",), [
            (0x20000000, 0x0),  # str r0, [r1, #0]
            (0x1000, 0x48),  # str r0, [r1, #0x48]
            (0x250, 0x7c),  # str r0, [r1, #0x7c]
        ])
    def test_str_imm_t1(self, cpu, fmt, addr, imm):
        Rn = 1
        Rt = 0
        cpu.r[Rt] = 0x12341234
        cpu.r[Rn] = addr
        i = decoder.decode(fmt_16bit('011 0 0 {imm5:5} {Rn:3} {Rt:3}', imm5=imm>>2, Rn=Rn, Rt=Rt))
        assert i.t == Rt
        assert i.n == Rn
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read32(addr + imm) == 0x12341234

    # str r0, [sp, #imm]
    @pytest.mark.parametrize(("addr", "imm",), [
            (0x20000000, 0x0),  # str r0, [sp, #0]
            (0x1000, 0x48),  # str r0, [sp, #0x48]
            (0x250, 0x7c),  # str r0, [sp, #0x7c]
        ])
    def test_str_imm_t2(self, cpu, fmt, addr, imm):
        Rt = 0
        cpu.r[13] = addr
        cpu.r[Rt] = 0x12341234
        i = decoder.decode(fmt_16bit('1001 0 {Rt:3} {imm8:8}', imm8=imm>>2, Rt=Rt))
        assert i.t == Rt
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read32(addr + imm) == 0x12341234

    # strh r0, [r1, #imm]
    @pytest.mark.parametrize(("addr", "imm",), [
            (0x20000000, 0x0),  # strh r0, [r1, #0]
            (0x20000000, 0x2),  # strh r0, [r1, #2]
            (0x1000, 0x18),  # strh r0, [r1, #0x18]
            (0x250, 0x38),  # strh r0, [r1, #0x38]
        ])
    def test_strh_imm_t1(self, cpu, fmt, addr, imm):
        Rn = 1
        Rt = 0
        cpu.r[Rt] = 0x12345678
        cpu.r[Rn] = addr
        i = decoder.decode(fmt_16bit('100 0 0 {imm5:5} {Rn:3} {Rt:3}', imm5=imm>>1, Rn=Rn, Rt=Rt))
        assert i.t == Rt
        assert i.n == Rn
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read16(addr + imm) == 0x5678

    # strb r0, [r1, #imm]
    @pytest.mark.parametrize(("addr", "imm",), [
            (0x20000000, 0x0),  # strb r0, [r1, #0]
            (0x20000000, 0x1),  # strb r0, [r1, #1]
            (0x1000, 28),  # strb r0, [r1, #28]
            (0x250, 31),  # strb r0, [r1, #31]
        ])
    def test_strb_imm_t1(self, cpu, fmt, addr, imm):
        Rn = 1
        Rt = 0
        cpu.r[Rt] = 0x12345678
        cpu.r[Rn] = addr
        i = decoder.decode(fmt_16bit('011 1 0 {imm5:5} {Rn:3} {Rt:3}', imm5=imm, Rn=Rn, Rt=Rt))
        assert i.t == Rt
        assert i.n == Rn
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.read8(addr + imm) == 0x78

class TestPush:
    def check_push(self, cpu, origSp, reglist):
        addr = origSp
        assert cpu.sp == origSp - 4 * reglist.bit_count()
        for i in range(15, -1, -1):
            if reglist[i]:
                addr -= 4
                assert cpu.read32(addr) == cpu.r[i]

    # push {r0,r1...r7}
    @pytest.mark.parametrize("m", [0, 1])
    def test_push_t1(self, cpu, fmt, m):
        for i in range(8):
            cpu.r[i] = i
        cpu.lr = 14
        reglist = bitstring('0000000011111001')
        reglist[14] = m
        i = decoder.decode(fmt_16bit('1011 0 10 {M} {reglist:8}', M=reglist[14], reglist=reglist[0:8]))
        print(fmt.format(i))
        sp = cpu.sp
        i.execute(cpu)
        self.check_push(cpu, sp, reglist)

    # push.w {r0,r1...r7}
    @pytest.mark.parametrize("m", [0, 1])
    def test_push_t2(self, cpu, fmt, m):
        for i in range(15):
            cpu.r[i] = i
        cpu.sp = 0x20004000
        reglist = bitstring('0000001111101011')
        reglist[14] = m
        i = decoder.decode(fmt_32bit('11101 00 100 1 0 1101, 0 {M} 0 {reglist:13}', M=reglist[14], reglist=reglist[0:13]))
        print(fmt.format(i))
        sp = cpu.sp
        i.execute(cpu)
        self.check_push(cpu, sp, reglist)

    # push.w {r0}
    def test_push_t2(self, cpu, fmt, reg4bit_nopc_nosp):
        for i in range(15):
            cpu.r[i] = i
        cpu.sp = 0x20004000
        reglist = zeros(16)
        reglist[reg4bit_nopc_nosp] = 1
        i = decoder.decode(fmt_32bit('11111 00 0 0 10 0 1101, {Rt:4} 1 101 00000100', Rt=reglist.lowest_set_bit()))
        print(fmt.format(i))
        sp = cpu.sp
        i.execute(cpu)
        self.check_push(cpu, sp, reglist)

class TestPop:
    def setup_stack(self, cpu, reglist):
        addr = cpu.sp
        for i in range(16):
            if reglist[i]:
                cpu.write32(addr, i)
                addr += 4

    def check_pop(self, cpu, origSp, reglist):
        addr = origSp
        assert cpu.sp == origSp + 4 * reglist.bit_count()
        for i in range(16):
            if reglist[i]:
                assert cpu.read32(addr) == cpu.r[i]
                addr += 4

    # pop {r0,r1...r7}
    @pytest.mark.parametrize("p", [0, 1])
    def test_pop_t1(self, cpu, fmt, p):
        reglist = bitstring('0000000011111001')
        reglist[15] = p
        self.setup_stack(cpu, reglist)
        i = decoder.decode(fmt_16bit('1011 1 10 {P} {reglist:8}', P=reglist[15], reglist=reglist[0:8]))
        print(fmt.format(i))
        sp = cpu.sp
        i.execute(cpu)
        self.check_pop(cpu, sp, reglist)

    # pop.w {r0,r1...r7}
    @pytest.mark.parametrize(("p", "m"), [
        (0, 0),
        (0, 1),
        (1, 0),
        ])
    def test_pop_t2(self, cpu, fmt, m, p):
        reglist = bitstring('0000001111101011')
        reglist[14] = m
        reglist[15] = p
        self.setup_stack(cpu, reglist)
        i = decoder.decode(fmt_32bit('11101 00 010 1 1 1101, {P} {M} 0 {reglist:13}', P=reglist[15], M=reglist[14], reglist=reglist[0:13]))
        print(fmt.format(i))
        sp = cpu.sp
        i.execute(cpu)
        self.check_pop(cpu, sp, reglist)

    # pop.w {r0}
    def test_pop_t3(self, cpu, fmt, reg4bit_nosp):
        reglist = zeros(16)
        reglist[reg4bit_nosp] = 1
        self.setup_stack(cpu, reglist)
        i = decoder.decode(fmt_32bit('11111 00 0 0 10 1 1101, {Rt:4} 1 011 00000100', Rt=reglist.lowest_set_bit()))
        print(fmt.format(i))
        sp = cpu.sp
        i.execute(cpu)
        self.check_pop(cpu, sp, reglist)

class TestStoreMultiple:
    def check_stm(self, cpu, Rn, wback, origAddr, reglist):
        addr = origAddr
        assert not wback or (cpu.r[Rn] == origAddr + 4 * reglist.bit_count())
        for i in range(16):
            if reglist[i]:
                assert cpu.read32(addr) == cpu.r[i]
                addr += 4

    def setup_regs(self, cpu):
        for i in range(15):
            if i != 13:
                cpu.r[i] = i

    # stm r2!, {r0,r1...r7}
    def test_stm_t1(self, cpu, fmt):
        self.setup_regs(cpu)
        Rn = 2
        reglist = bitstring('0000000011111001')
        cpu.r[Rn] = 0x20001000
        i = decoder.decode(fmt_16bit('1100 0 {Rn:3} {reglist:8}', Rn=Rn, reglist=reglist[0:8]))
        print(fmt.format(i))
        origAddr = cpu.r[Rn]
        i.execute(cpu)
        self.check_stm(cpu, Rn, True, origAddr, reglist)

    # stm.w r2{!}, {r0,r1...r7}
    @pytest.mark.parametrize(("W", "M"), [
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 1),
        ])
    def test_stm_t2(self, cpu, fmt, W, M):
        self.setup_regs(cpu)
        Rn = 2
        reglist = bitstring('0000001111101011')
        reglist[14] = M
        cpu.r[Rn] = 0x20001000
        i = decoder.decode(fmt_32bit('11101 00 010 {W} 0 {Rn:4}, 0 {M} 0 {reglist:13}', Rn=Rn, W=W, M=reglist[14], reglist=reglist[0:13]))
        print(fmt.format(i))
        origAddr = cpu.r[Rn]
        i.execute(cpu)
        self.check_stm(cpu, Rn, W, origAddr, reglist)

class TestLoadMultiple:
    def setup_stack(self, cpu, Rn, reglist):
        addr = cpu.r[Rn]
        for i in range(16):
            if reglist[i]:
                if i in (13, 15):
                    cpu.write32(addr, cpu.r[i])
                else:
                    cpu.write32(addr, i)
                addr += 4

    def check_ldm(self, cpu, Rn, wback, origAddr, reglist):
        addr = origAddr
        assert not wback or (cpu.r[Rn] == origAddr + 4 * reglist.bit_count())
        for i in range(16):
            if reglist[i]:
                assert cpu.read32(addr) == cpu.r[i]
                addr += 4

    # ldm r3, {r0,r1...r7}
    @pytest.mark.parametrize("W", [0, 1])
    def test_ldm_t1(self, cpu, fmt, W):
        Rn = 3
        reglist = bitstring('0000000011111001')
        reglist[Rn] = 0 if W else 1
        cpu.r[Rn] = 0x20001000
        self.setup_stack(cpu, Rn, reglist)
        i = decoder.decode(fmt_16bit('1100 1 {Rn:3} {reglist:8}', Rn=Rn, reglist=reglist[0:8]))
        print(fmt.format(i))
        origAddr = cpu.r[Rn]
        i.execute(cpu)
        self.check_ldm(cpu, Rn, W, origAddr, reglist)

    # ldm.w r2{!}, {r0,r1...r7}
    @pytest.mark.parametrize(("W", "P", "M"), [
            (0, 0, 0),
            (0, 0, 1),
            (0, 1, 0),
            (1, 0, 0),
            (1, 0, 1),
            (1, 1, 0),
        ])
    def test_ldm_t2(self, cpu, fmt, W, P, M):
        Rn = 2
        reglist = bitstring('0000001111101011')
        reglist[15] = P
        reglist[14] = M
        cpu.r[Rn] = 0x20001000
        self.setup_stack(cpu, Rn, reglist)
        i = decoder.decode(fmt_32bit('11101 00 010 {W} 1 {Rn:4}, {P} {M} 0 {reglist:13}', Rn=Rn, W=W, P=reglist[15], M=reglist[14], reglist=reglist[0:13]))
        print(fmt.format(i))
        origAddr = cpu.r[Rn]
        i.execute(cpu)
        self.check_ldm(cpu, Rn, W, origAddr, reglist)

class TestCps:
    @pytest.mark.parametrize(("enable", "I", "F"), [
            (False, 1, 0),
            (False, 0, 1),
            (False, 1, 1),
            (True, 1, 0),
            (True, 0, 1),
            (True, 1, 1),
        ])
    def test_cps(self, cpu, fmt, enable, I, F):
        im = 0 if enable else 1
        inv_im = 0 if im else 1
        cpu.write_register(CORE_REGISTER['primask'], inv_im)
        cpu.write_register(CORE_REGISTER['faultmask'], inv_im)
        i = decoder.decode(fmt_16bit('1011 0110 011 {im} 0 0 {I} {F}', im=im, I=I, F=F))
        print(fmt.format(i))
        i.execute(cpu)
        if I:
            assert cpu.read_register(CORE_REGISTER['primask']) == im
        else:
            assert cpu.read_register(CORE_REGISTER['primask']) == inv_im
        if F:
            assert cpu.read_register(CORE_REGISTER['faultmask']) == im
        else:
            assert cpu.read_register(CORE_REGISTER['faultmask']) == inv_im

class TestBkpt:
    @pytest.mark.parametrize("imm", [0, 0xab])
    def test_bkpt(self, cpu, fmt, imm):
        i = decoder.decode(fmt_16bit('1011 1110 {imm8:8}', imm8=imm))
        assert i.imm32 == imm
        print(fmt.format(i))
        i.execute(cpu)

class TestNopHints:
    @pytest.mark.parametrize("x", [0, 1, 2, 3, 4])
    def test_mov_reg_t3_1(self, cpu, fmt, x):
        i = decoder.decode(fmt_16bit('1011 1111 {x:4} 0000', x=x))
        print(fmt.format(i))
        i.execute(cpu)

class TestBarriers:
    @pytest.mark.parametrize(("x", "option"), [
            (0, 0b1111), # dsb sy
            (1, 0b1111), # dmb sy
            (2, 0b1111), # isb sy
            (0, 8), # dsb #8
            (1, 9), # dmb #9
            (2, 10), # isb #10
        ])
    def test_mov_reg_t3_1(self, cpu, fmt, x, option):
        i = decoder.decode(fmt_32bit('11110 0 111 01 1 1111, 10 0 0 1111 01{x:2} {option:4}', x=x, option=option))
        print(fmt.format(i))
        i.execute(cpu)

class TestSpecialRegister:
    @pytest.fixture(params=[
            0, # APSR
            1, # IAPSR
            2, # EAPSR
            3, # XPSR
            5, # IPSR
            6, # EPSR
            7, # IEPSR
            8, # MSP
            9, # PSP
            16, # PRIMASK
            17, # BASEPRI
            18, # BASEPRI_MAX
            19, # FAULTMASK
            20, # CONTROL
        ])
    def SYSm(self, request):
        return request.param

    # mrs r3, <spec>
    def test_mrs(self, cpu, fmt, SYSm):
        Rd = 3
        i = decoder.decode(fmt_32bit('11110 0 1111 1 0 1111, 10 0 0 {Rd:4} {SYSm:8}', Rd=Rd, SYSm=SYSm))
        print(fmt.format(i))
#         i.execute(cpu)

    # msr <spec>, r3
    def test_msr(self, cpu, fmt, SYSm):
        Rn = 3
        mask = 2 # _nzcvq
        i = decoder.decode(fmt_32bit('11110 0 1110 0 0 {Rn:4}, 10 0 0 {mask:2} 0 0 {SYSm:8}', Rn=Rn, mask=mask, SYSm=SYSm))
        print(fmt.format(i))
#         i.execute(cpu)

class TestMisc:
    def test_svc_t1(self, cpu, fmt):
        imm8 = 72
        i = decoder.decode(fmt_16bit('1101 1111 {imm8:8}', imm8=imm8))
        print(fmt.format(i))
#         i.execute(cpu)

    def test_udf_t1(self, cpu, fmt):
        imm8 = 60
        i = decoder.decode(fmt_16bit('1101 1110 {imm8:8}', imm8=imm8))
        print(fmt.format(i))
#         i.execute(cpu)

    def test_udf_t2(self, cpu, fmt):
        imm = bitstring(1234)
        i = decoder.decode(fmt_32bit('111 10 1111111 {imm4:4}, 1 010 {imm12:12}', imm4=imm[12:16], imm12=imm[0:12]))
        print(fmt.format(i))
#         i.execute(cpu)

