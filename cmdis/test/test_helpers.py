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
from ..helpers import *

class TestAddWithCarry:
    def test_0(self):
        x = bitstring('00000')
        y = bitstring('00000')
        assert AddWithCarry(x, y, bit0) == (0, 0, 0)

    def test_1(self):
        x = bitstring('00001')
        y = bitstring('00000')
        assert AddWithCarry(x, y, bit0) == (1, 0, 0)

    def test_1p1(self):
        x = bitstring('00001')
        y = bitstring('00001')
        assert AddWithCarry(x, y, bit0) == (2, 0, 0)

    def test_a(self):
        x = bitstring('00101')
        y = bitstring('00011')
        assert AddWithCarry(x, y, bit0) == ('01000', 0, 0)

    def test_carry_0(self):
        x = bitstring('00000')
        y = bitstring('00000')
        assert AddWithCarry(x, y, bit1) == ('00001', 0, 0)

    def test_b(self):
        x = bitstring(5432)
        y = bitstring(143223)
        assert AddWithCarry(x, y, bit0) == (148655, 0, 0)

    def test_c(self):
#         x = bitstring()
        pass

class TestLSL:
    def test_0(self):
        assert LSL_C(bitstring('1001'), 1) == ('0010', '1')

    def test_1(self):
        assert LSL_C(bitstring('0001'), 1) == ('0010', '0')

class TestLSR:
    def test_0(self):
        assert LSR_C(bitstring('1001'), 1) == ('0100', '1')

    def test_1(self):
        assert LSR_C(bitstring('0100'), 1) == ('0010', '0')

class TestASR:
    def test_0(self):
        assert ASR_C(bitstring('1001000'), 1) == ('1100100', '0')

    def test_1(self):
        assert ASR_C(bitstring('0100000'), 1) == ('0010000', '0')

    def test_2(self):
        assert ASR_C(bitstring('0100001'), 1) == ('0010000', '1')

    def test_3(self):
        assert ASR_C(bitstring('1001001'), 1) == ('1100100', '1')

    def test_4(self):
        assert ASR_C(bitstring('1001001'), 4) == ('1111100', '1')

class TestROR:
    def test_0(self):
        assert ROR_C(bitstring('1001'), 1) == ('1100', '1')

    def test_1(self):
        assert ROR_C(bitstring('0100'), 1) == ('0010', '0')

class TestRRX:
    def test_0(self):
        assert RRX_C(bitstring('1001'), bit0) == ('0100', '1')

    def test_1(self):
        assert RRX_C(bitstring('0100'), bit1) == ('1010', '0')

    def test_2(self):
        assert RRX_C(bitstring('0111'), bit1) == ('1011', '1')

    def test_3(self):
        assert RRX_C(bitstring('0110'), bit0) == ('0011', '0')

class TestDecodeImmShift:
    def test_lsl(self):
        assert DecodeImmShift(bitstring('00'), bitstring('00000')) == (SRType.SRType_LSL, 0)
        assert DecodeImmShift(bitstring('00'), bitstring('00001')) == (SRType.SRType_LSL, 1)
        assert DecodeImmShift(bitstring('00'), bitstring('11111')) == (SRType.SRType_LSL, 31)

    def test_lsr(self):
        assert DecodeImmShift(bitstring('01'), bitstring('00000')) == (SRType.SRType_LSR, 32)
        assert DecodeImmShift(bitstring('01'), bitstring('00001')) == (SRType.SRType_LSR, 1)
        assert DecodeImmShift(bitstring('01'), bitstring('11111')) == (SRType.SRType_LSR, 31)

    def test_asr(self):
        assert DecodeImmShift(bitstring('10'), bitstring('00000')) == (SRType.SRType_ASR, 32)
        assert DecodeImmShift(bitstring('10'), bitstring('00001')) == (SRType.SRType_ASR, 1)
        assert DecodeImmShift(bitstring('10'), bitstring('11111')) == (SRType.SRType_ASR, 31)

    def test_rrx(self):
        assert DecodeImmShift(bitstring('11'), bitstring('00000')) == (SRType.SRType_RRX, 1)

    def test_ror(self):
        assert DecodeImmShift(bitstring('11'), bitstring('00001')) == (SRType.SRType_ROR, 1)
        assert DecodeImmShift(bitstring('11'), bitstring('11111')) == (SRType.SRType_ROR, 31)

