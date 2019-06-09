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

from __future__ import print_function
import string
import functools
from collections import (defaultdict, namedtuple)

from .bitstring import bitstring
from .utilities import (bytes_to_le16, hamming_weight)
from .formatter import Formatter

##
# @brief Base class for a decoded instruction.
class Instruction(object):
    def __init__(self, mnemonic, word, is32bit):
        self._mnemonic = mnemonic
        self._word = word
        self._is32bit = is32bit
        self._address = 0
        self.operands = []

    @property
    def mnemonic(self):
        return self._mnemonic

    @property
    def size(self):
        return 4 if self._is32bit else 2

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def bytes(self):
        return bytearray((self._word >> (8 * i)) & 0xff for i in range(self.size))

    def _eval(self, cpu):
        cpu.pc += self.size

    def execute(self, cpu):
        return self._eval(cpu)

    def __repr__(self):
        i = (" %08x" if self._is32bit else " %04x") % self._word
        return "<Instruction@0x%x %s %s>" % (id(self), self._mnemonic, i)

# A node of the decoder tree pairs a mask with a dictionary of child nodes. The dict
# keys are the unique values for the mask. If the mask value is 0, then the node is a
# leaf node and there is only one child.
DecoderTreeNode = namedtuple('DecoderTreeNode', 'mask children')

##
# @brief Exception raised when an instruction cannot be decoded successfully.
class UndefinedInstructionError(Exception):
    pass

##
# @brief Selected decoder doesn't match, move on.
class DecodeError(Exception):
    pass

##
# @brief Effects of an instruction encoding are unpredictable.
class UnpredictableError(Exception):
    pass

##
# @brief Interface for decoding instruction byte sequences.
#
# Tree-based instruction decoding algorithm borrowed from Amoco project by Axel Tillequin
# (bdcht3@gmail.com) and re-written.
class DecoderTree(object):

    _32bitMask = 0xf800
    _32bitPrefixes = [0xf800, 0xf000, 0xe800]

    def __init__(self):
        self._decoders16 = []
        self._decoders32 = []
        self._tree16 = None
        self._tree32 = None

    def add_decoder(self, decoder):
        if decoder.is32bit:
            self._decoders32.append(decoder)
        else:
            self._decoders16.append(decoder)

    def build(self):
        self._tree16 = self._build_tree(self._decoders16)
        self._tree32 = self._build_tree(self._decoders32)

    def decode(self, data, dataAddress=0):
        # Figure out if this is a 16-bit or 32-bit instruction and select the
        # appropriate decoder tree.
        assert len(data) >= 2
        hw1 = bytes_to_le16(data)
        is32bit = hw1 & self._32bitMask in self._32bitPrefixes
        if is32bit:
            if len(data) < 4:
                raise UndefinedInstructionError()
            hw2 = bytes_to_le16(data, 2)
            word = hw1 | (hw2 << 16)
            node = self._tree32
        else:
            word = hw1
            node = self._tree16

        while True:
            if node.mask:
                try:
                    node = node.children[word & node.mask]
                except KeyError:
                    # Couldn't find a matching instruction.
                    raise UndefinedInstructionError()
            else:
                for d in node.children:
                    try:
                        if d.check(word):
                            return d.decode(word, address=dataAddress)
                    except DecodeError:
                        continue

                # None of the decoders matched.
                raise UndefinedInstructionError()

    def _build_tree(self, decoders):
        # Sort decoders in descending order of number of bits set in the mask.
        # This sorting is required for proper computation of the common mask.
        decoders = sorted(decoders, key=lambda d:hamming_weight(d._mask), reverse=True)

        # If there is only one decoder at this level, there is nothing left to do.
        if len(decoders) < 2:
            return DecoderTreeNode(mask=0, children=decoders)

        # Compute the mask of common bits that all decoders at this level have set.
        commonMask = functools.reduce(lambda a, b: a & b, [d._mask for d in decoders])
        if commonMask == 0:
            return DecoderTreeNode(mask=commonMask, children=decoders)

        # Find all decoders that have the same match values masked by the common mask.
        children = defaultdict(list)
        for decoder in decoders:
            children[decoder._match & commonMask].append(decoder)

        # If there is only one element in the children dict, then all decoders at this
        # level have the same value under the common mask.
        if len(children) == 1:
            return DecoderTreeNode(mask=0, children=list(children.values())[0])

        # Recursively process each group of children with the same match value at this level.
        for k, subdecoders in children.items():
            children[k] = self._build_tree(subdecoders)

        return DecoderTreeNode(mask=commonMask, children=children)

    def dump(self, t=None, depth=0):
        if t is None:
            print("16-bit instructions:")
            self.dump(self._tree16)
            print("32-bit instructions:")
            self.dump(self._tree32)
        else:
            mask, nodes = t.mask, t.children
            print("  " * depth, hex(mask), "=>")
            if type(nodes) is list:
                for i,d in enumerate(nodes):
                    print("  " * (depth + 1), i, ":", d)
            else:
                for i,k in enumerate(nodes.iterkeys()):
                    print("  " * (depth + 1), i, ":", hex(k))
                    self.dump(nodes[k], depth+2)

DECODER_TREE = DecoderTree()

##
# @brief
class Decoder(object):
    def __init__(self, handler, mnemonic, klass, spec, spec2=None, **kwargs):
        self._handler = handler
        self._mnemonic = mnemonic
        self._klass = klass
        self.spec = spec
        self.spec2 = spec2
        self.args = kwargs

        fmt = parse_spec(self.spec)
        fmt.reverse()
        self._mask, self._match, self._attrs = self.process_fmt(fmt)
        if self.spec2 is not None:
            fmt2 = parse_spec(self.spec2)
            fmt2.reverse()
            mask2, match2, attrs2 = self.process_fmt(fmt2, offset=16)
            self._mask |= mask2
            self._match |= match2
            self._attrs.update(attrs2)
            self.is32bit = True
        else:
            self.is32bit = False

    def check(self, word):
        return (word & self._mask) == self._match

    def decode(self, word, address=0):
        # Read bitfields from the instruction.
        attrs = {}
        for n,f in self._attrs.items():
            attrs[n] = f(word)

        # Create instruction object.
        i = self._klass(self._mnemonic, word, self.is32bit)
        i.address = address
        for k, v in self.args.items():
            setattr(i, k, v)

        # Call handler to further decode instruction.
        self._handler(i, **attrs)

        return i

    def __repr__(self):
        return "<Decoder@0x%x %s %x/%x %s>" % (id(self), self._mnemonic, self._mask, self._match, self._attrs.keys())

    def process_fmt(self, fmt, offset=0):
        i = 0
        mask = 0
        match = 0
        d = {}
        for f in fmt:
            if f in (0, 1):
                # Update mask and match values with fixed bit.
                mask |= 1 << i+offset
                match |= f << i+offset
                i += 1
            elif type(f) is tuple:
                name, value = f
                if isinstance(value, bitstring):
                    mask |= value.mask << i+offset
                    match |= value.unsigned << i+offset
                    size = value.width
                else:
                    size = value
                # Put a lambda to extract this named field from the instruction word into the d dict.
                d[name] = lambda b,i=i+offset,size=size: bitstring(b >> i, size)
                i += size
            else:
                raise ValueError("unexpected format element in spec: %s" % f)
        assert i == 16, "format was not exactly 16 bits (was %d)" % i
        return mask, match, d

##
# @brief Decorator to build Decoder object from instruction format strings.
def instr(mnemonic, klass, spec, spec2=None, **kwargs):
    def doit(fn):
        DECODER_TREE.add_decoder(Decoder(fn, mnemonic, klass, spec, spec2, **kwargs))
        return fn
    return doit


# Grammar:
#
# start         => field*
#
# field         => bit | value
#
# bit           => '0' | '1'
#
# value         => ident ( '(' intlit ')' )?
#               => ident '=' bits
#
# bits          => bit+         ; terminates on first non-bit char
#
# ident         => /[a-zA-Z][a-zA-Z0-9]*/
#
# intlit        => /[0-9]+/
#
def parse_spec(spec):
    result = []
    i = 0
    state = 0
    ident = ''
    bitcount = ''
    bits = ''
    expectingBitcount = False
    while i < len(spec):
        c = spec[i]

        # Default state.
        if state == 0:
            if c in ('0', '1'):
                if ident:
                    result.append((ident, 1))
                    ident = ''
                result.append(int(c))
                expectingBitcount = False
            elif c in string.ascii_letters:
                if ident:
                    result.append((ident, 1))
                    ident = ''
                ident = c
                state = 1
            elif c == '(' and expectingBitcount:
                state = 2
            elif c in string.whitespace:
                pass
            else:
                raise ValueError("unexpected character '%s' at position %d" % (c, i))
        # Ident state.
        elif state == 1:
            if c == '(':
                state = 2
            elif c == '=':
                bits = ''
                state = 5
            elif c not in string.ascii_letters + string.digits:
                # Switch to default state and back up.
                state = 0
                i -= 1
                expectingBitcount = True
            else:
                ident += c
        # Enter bitcount state.
        elif state == 2:
            if c in string.digits:
                bitcount = c
                state = 3
            elif c == ')':
                bitcount = '1'
                state = 0
            elif c in string.whitespace:
                pass
            else:
                raise ValueError("unexpected character '%s' at position %d" % (c, i))
        # Bitcount state.
        elif state == 3:
            if c == ')':
                result.append((ident, int(bitcount)))
                ident = ''
                bitcount = ''
                state = 0
            elif c not in string.digits:
                state = 4
            else:
                bitcount += c
        # Close bitcount state.
        elif state == 4:
            if c == ')':
                result.append((ident, int(bitcount)))
                ident = ''
                bitcount = ''
                state = 0
            elif c in string.whitespace:
                pass
            else:
                raise ValueError("unexpected character '%s' at position %d" % (c, i))
        # Fixed value state.
        elif state == 5:
            if c in ('0', '1'):
                bits += c
            else:
                result.append((ident, bitstring(bits)))
                bits = ''
                ident = ''
                state = 0

        i += 1

    if ident:
        if bits:
            result.append((ident, bitstring(bits)))
        else:
            if not bitcount:
                bitcount = '1'
            result.append((ident, int(bitcount)))

    return result


