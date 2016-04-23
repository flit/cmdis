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

