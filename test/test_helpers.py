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

from cmdis.bitstring import *
from cmdis.helpers import *

class TestAlign:
    def test_0(self):
        assert Align(0x1001, 4) == 0x1000

    def test_1(self):
        assert Align(0x1003, 4) == 0x1000

    def test_2(self):
        assert Align(0x1003, 2) == 0x1002

    def test_3(self):
        assert Align(0x1007, 16) == 0x1000

    def test_4(self):
        assert Align(bitstring(0x1001), 4) == bitstring(0x1000)

    def test_5(self):
        assert Align(bitstring(0x1003), 4) == bitstring(0x1000)

    def test_6(self):
        assert Align(bitstring(0x1003), 2) == bitstring(0x1002)

    def test_7(self):
        assert Align(bitstring(0x1007), 16) == bitstring(0x1000)

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

class TestThumbExpandImm:
    def test_a(self):
        pass

