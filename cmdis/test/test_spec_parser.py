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

from ..decoder import parse_spec

class TestParser:
    def test_a(self):
        r = parse_spec('0010 0 1')
        assert r == [0, 0, 1, 0, 0, 1]

    def test_b(self):
        r = parse_spec('0110 1 Rd(3) imm8(8)')
        assert r == [0, 1, 1, 0, 1, ('Rd', 3), ('imm8', 8)]

    def test_c(self):
        r = parse_spec('0110 S imm8(8)')
        assert r == [0, 1, 1, 0, ('S', 1), ('imm8', 8)]

    def test_d(self):
        r = parse_spec('0110 imm8(8) S')
        assert r == [0, 1, 1, 0, ('imm8', 8), ('S', 1)]

    def test_e(self):
        r = parse_spec('0110 S() imm8(8)')
        assert r == [0, 1, 1, 0, ('S', 1), ('imm8', 8)]

    def test_f(self):
        r = parse_spec('0110 imm8(8) S()')
        assert r == [0, 1, 1, 0, ('imm8', 8), ('S', 1)]

    def test_g(self):
        r = parse_spec('0110 imm8(8) S() 11 00')
        assert r == [0, 1, 1, 0, ('imm8', 8), ('S', 1), 1, 1, 0, 0]

    def test_h(self):
        r = parse_spec('Q imm7(7) S(1)')
        assert r == [('Q', 1), ('imm7', 7), ('S', 1)]

    def test_i(self):
        r = parse_spec('Q imm7 ( 7 ) S ( 1 )')
        assert r == [('Q', 1), ('imm7', 7), ('S', 1)]

    def test_j(self):
        r = parse_spec('Q( ) imm12 ( 12 ) S')
        assert r == [('Q', 1), ('imm12', 12), ('S', 1)]

    def test_k(self):
        r = parse_spec(' Q( ) imm12 ( 12 ) S  ')
        assert r == [('Q', 1), ('imm12', 12), ('S', 1)]

