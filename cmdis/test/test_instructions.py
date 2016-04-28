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
import pytest
import string
import six

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
            elif c in string.whitespace:
                pass
            else:
                result += c
        elif state == 1:
            if c in string.ascii_letters:
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
    c.pc = 0x8000
    c.sp = 0x20004000
    return c

@pytest.fixture(scope='function')
def fmt(cpu):
    return Formatter(cpu)

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

    # mov.w r12, r2
    @pytest.mark.parametrize("S", [0, 1])
    def test_mov_reg_t3_1(self, cpu, fmt, S):
        cpu.r[2] = bitstring(0x1234)
        i = decoder.decode(fmt_32bit('11101010010{S}1111,0000110000000010', S=S))
        assert i.m == 2
        assert i.d == 12
        print(fmt.format(i))
        i.execute(cpu)
        assert cpu.r[12] == 0x1234

    # mov.w r3, #7
#     def test_mov_t1(self, cpu, fmt):
#         i = decoder.decode(le16_to_bytes(0b11110))
#         assert i.imm32 == 7
#         assert i.d == 1
#         print(fmt.format(i))
#         i.execute(cpu)
#         assert cpu.r[3] == 7

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


