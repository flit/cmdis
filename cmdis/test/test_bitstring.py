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

