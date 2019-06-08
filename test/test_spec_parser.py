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

from ..decoder import parse_spec
from ..bitstring import bitstring

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

    def test_l(self):
        r = parse_spec('0001 foo=0100 imm8(8)')
        assert r == [0, 0, 0, 1, ('foo', bitstring('0100')), ('imm8', 8)]

    def test_m(self):
        r = parse_spec('0001 foo=0 imm8(8)')
        assert r == [0, 0, 0, 1, ('foo', bitstring('0')), ('imm8', 8)]

    def test_n(self):
        r = parse_spec('0001 foo=1 imm8(8)')
        assert r == [0, 0, 0, 1, ('foo', bitstring('1')), ('imm8', 8)]

    def test_o(self):
        r = parse_spec('0001 foo=1 imm8(8) baz=100')
        assert r == [0, 0, 0, 1, ('foo', bitstring('1')), ('imm8', 8), ('baz', bitstring('100'))]

