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

from ..bitstring import bitstring

class TestBitstring:
    def test_init_empty(self):
        b = bitstring()
        assert b.width == 0
        assert b.value == 0
        assert b.mask == 0

        b = bitstring(width=8)
        assert b.width == 8
        assert b.value == 0
        assert b.mask == 0xff

    def test_init_int1(self):
        b = bitstring(1, 1)
        assert b.width == 1
        assert b.value == 1
        assert b.mask == 1

        b = bitstring(1L, 1)
        assert b.width == 1
        assert b.value == 1
        assert b.mask == 1

    def test_init_int2(self):
        b = bitstring(1, 32)
        assert b.width == 32
        assert b.value == 1
        assert b.mask == 0xffffffff

        b = bitstring(1L, 32)
        assert b.width == 32
        assert b.value == 1
        assert b.mask == 0xffffffff

    def test_init_int_default_width(self):
        b = bitstring(1)
        assert b.width == 32
        assert b.value == 1
        assert b.mask == 0xffffffff

        b = bitstring(1 << 48)
        assert b.width == 64
        assert b.value == 1 << 48
        assert b.mask == (1<<64) - 1

        b = bitstring(1L)
        assert b.width == 32
        assert b.value == 1
        assert b.mask == 0xffffffff

    def test_init_int_masked(self):
        b = bitstring(65535, 8)
        assert b.width == 8
        assert b.value == 255
        assert b.mask == 0xff

    def test_init_str(self):
        b = bitstring('100', 3)
        assert b.width == 3
        assert b.value == 4
        assert b.mask == 0b111

        b = bitstring('100')
        assert b.width == 3
        assert b.value == 4
        assert b.mask == 0b111

    def test_init_large_int(self):
        b = bitstring(1<<127, 128)
        assert b.width == 128
        assert b.value == 1<<127
        assert b.mask == (1<<128) - 1

    def test_init_iter(self):
        b = bitstring([0, 1, 0, 0, 1])
        assert b.width == 5
        assert b.value == 0b01001
        assert b.mask == 0b11111

        b = bitstring([0, 1, 0, 0, 1], width=5)
        assert b.width == 5
        assert b.value == 0b01001
        assert b.mask == 0b11111

        b = bitstring([0, 1, 0, 0, 1], width=8)
        assert b.width == 8
        assert b.value == 0b01001
        assert b.mask == 0b11111111

    def test_value_setter(self):
        b = bitstring(0)
        assert b.width == 32
        assert b.value == 0
        b.value = 1234
        assert b.value == 1234

        b = bitstring(0, width=8)
        assert b.width == 8
        assert b.value == 0
        b.value = 1234567
        assert b.value == 135

    def test_width_setter(self):
        b = bitstring(0)
        assert b.width == 32
        assert b.value == 0
        b.width = 16
        assert b.width == 16
        assert b.mask == 0xffff
        assert b.value == 0

        b = bitstring(127, 16)
        b.width = 8
        assert b.value == 127
        assert b.width == 8
        assert b.mask == 0xff

        b = bitstring(1234567)
        b.width = 8
        assert b.value == 135
        assert b.mask == 0xff
        b.width = 20
        assert b.value == 135
        assert b.mask == (1 << 20) - 1

    def test_is_zero(self):
        assert bitstring('00000').is_zero()
        assert not bitstring('0010').is_zero()

    def test_is_ones(self):
        assert not bitstring('0000').is_ones()
        assert bitstring('1111').is_ones()

    def test_bit_count(self):
        assert bitstring('0').bit_count() == 0
        assert bitstring('1').bit_count() == 1
        assert bitstring(0, 0).bit_count() == 0
        assert bitstring('000000').bit_count() == 0
        assert bitstring('100000').bit_count() == 1
        assert bitstring('010101').bit_count() == 3
        assert bitstring('111111').bit_count() == 6

    def test_lowest_set(self):
        assert bitstring('000000').lowest_set_bit() == 6
        assert bitstring('000001').lowest_set_bit() == 0
        assert bitstring('100000').lowest_set_bit() == 5
        assert bitstring('101100').lowest_set_bit() == 2

    def test_highest_set(self):
        assert bitstring('000000').highest_set_bit() == -1
        assert bitstring('000001').highest_set_bit() == 0
        assert bitstring('010001').highest_set_bit() == 4
        assert bitstring('101011').highest_set_bit() == 5

    def test_sign_extend(self):
        assert bitstring('00001').sign_extend(8) == bitstring('00000001')
        assert bitstring('1000').sign_extend(8) == bitstring('11111000')

    def test_zero_extend(self):
        assert bitstring('00001').zero_extend(8) == bitstring('00000001')
        assert bitstring('1000').zero_extend(8) == bitstring('00001000')

    def test_invert(self):
        assert bitstring('1').invert() == bitstring('0')
        assert bitstring('0').invert() == bitstring('1')
        assert bitstring('0010010').invert() == bitstring('1101101')

    def test_append(self):
        assert bitstring() + bitstring('0') == bitstring('0')
        assert bitstring('01001') + bitstring('11110') == bitstring('0100111110')

    def test_eq(self):
        assert bitstring('0') == 0
        assert bitstring('1') == 1
        assert bitstring('0') == bitstring('0')
        assert bitstring('1') == bitstring('1')
        assert bitstring('0') == '0'
        assert bitstring('1') == '1'
        assert bitstring('1010') == '1010'
        assert bitstring('000100') == bitstring('000100')
        assert bitstring('000100') == 4

    def test_append(self):
        b = bitstring('1010')
        c = b % bitstring('111')
        assert c == '1010111'
        b %= '0011'
        assert b == '10100011'

    def test_lshift(self):
        assert bitstring('1100') << 4 == '0000'
        b = bitstring('1011')
        b <<= 3
        assert b == '1000'

    def test_rshift(self):
        assert bitstring('110011') >> 2 == '001100'
        b = bitstring('10101011')
        b >>= 4
        assert b == '00001010'

    def test_and(self):
        assert bitstring('0') & bitstring('0') == '0'
        assert bitstring('1') & bitstring('1') == '1'
        assert bitstring('1') & bitstring('0') == '0'
        assert bitstring('1001010') & '0011100' == '0001000'
        assert bitstring('100') & 4 == 4
        b = bitstring('10011')
        b &= '11111'
        assert b == '10011'

    def test_or(self):
        assert bitstring('0') | bitstring('0') == '0'
        assert bitstring('1') | bitstring('1') == '1'
        assert bitstring('1') | bitstring('0') == '1'
        assert bitstring('1001010') | '0011100' == '1011110'
        assert bitstring('100') | 4 == 4
        b = bitstring('10011')
        b |= '11111'
        assert b == '11111'

    def test_xor(self):
        assert bitstring('0') ^ bitstring('0') == '0'
        assert bitstring('1') ^ bitstring('1') == '0'
        assert bitstring('1') ^ bitstring('0') == '1'
        assert bitstring('1001010') ^ '0011100' == '1010110'
        assert bitstring('100') ^ 4 == 0
        b = bitstring('10011')
        b ^= '11111'
        assert b == '01100'

    def test_add(self):
        assert bitstring('001') + bitstring('001') == '010'
        assert bitstring('110') + bitstring('011') == '001'
        assert bitstring('010') + '001' == '011'
        b = bitstring('0010')
        b += 4
        assert b == '0110'

    def test_sub(self):
        assert bitstring('110') - bitstring('001') == '101'
        assert bitstring('001') - '001' == '000'
        b = bitstring('0010')
        b -= 4
        assert b == '1110'

    def test_mul(self):
        assert bitstring('110') * bitstring('001') == '110'
        assert bitstring('010') * '011' == '110'
        b = bitstring('0010')
        b *= 4
        assert b == '1000'

    def test_floordiv(self):
        assert bitstring('110') // bitstring('001') == '110'
        assert bitstring('110') // '010' == '011'
        b = bitstring('1000')
        b //= 4
        assert b == '0010'

    def test_getitem(self):
        x = bitstring('11001')
        assert x[0] == '1'
        assert x[1] == '0'
        assert x[2] == '0'
        assert x[-1] == '1'
        assert x[-2] == '1'

    def test_slice(self):
        x = bitstring('11001')
        assert x[0:1] == '1'
        assert x[0:x.width] == '11001'
        assert x[2:5] == '110'

    def test_bytes(self):
        x = bitstring(0x563924)
        assert x.bytes == bytearray([0x24, 0x39, 0x56, 0x00])
        x.width = 16
        assert x.bytes == bytearray([0x24, 0x39])
        x.width = 5
        assert x.bytes == bytearray([0x04])


