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

from .model import Instruction
import string
from collections import (defaultdict, namedtuple)

# DECODERS = []

DecoderTreeNode = namedtuple('DecoderTreeNode', 'mask children')

_32bitMask = 0xf800
_32bitPrefixes = [0xf800, 0xf000, 0xe800]

def hamming_weight(v):
    weight = 0
    while v != 0:
        weight += v & 1
        v >>= 1
    return weight

def bytes_to_le16(data, offset=0):
    return data[offset] | (data[offset+1] << 8)

class UndefinedInstructionError(Exception):
    pass

##
# @brief
#
# Tree-based instruction decoding algorithm borrowed from Amoco project by Axel Tillequin
# (bdcht3@gmail.com) and re-written.
class DecoderTree(object):
    def __init__(self):
        self._decoders16 = []
        self._decoders32 = []
        self._tree16 = None #self._build_tree()
        self._tree32 = None

    def add_decoder(self, decoder):
        if decoder.is32bit:
            self._decoders32.append(decoder)
        else:
            self._decoders16.append(decoder)

    def build(self):
        self._tree16 = self._build_tree(self._decoders16)
        self._tree32 = self._build_tree(self._decoders32)

    def decode(self, data):
        assert len(data) >= 2
        hw1 = bytes_to_le16(data)
        is32bit = hw1 & _32bitMask in _32bitPrefixes
        hw2 = bytes_to_le16(data, 2) if is32bit else None
        if is32bit:
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
                assert len(node.children) == 1
                return node.children[0].decode(word, hw2)

    def _build_tree(self, decoders):
        # Sort decoders in descending order of number of bits set in the mask.
        decoders = sorted(decoders, key=lambda d:hamming_weight(d._mask), reverse=True)

        if len(decoders) < 2:
            return DecoderTreeNode(mask=0, children=decoders)

        # Compute the mask that all decoders at this level have set.
        mergedMask = reduce(lambda a, b: a & b, [d._mask for d in decoders])
        if mergedMask == 0:
            return DecoderTreeNode(mask=mergedMask, children=decoders)

        # Find all decoders that have matching values under the merged mask.
        children = defaultdict(lambda :list())
        for decoder in decoders:
            children[decoder._match & mergedMask].append(decoder)
        if len(children) == 1:
            return DecoderTreeNode(mask=0, children=children.values())

        # Recursively process each group of children with the same match value at this level.
        for k, subdecoders in children.iteritems():
            children[k] = self._build_tree(subdecoders)

        return DecoderTreeNode(mask=mergedMask, children=children)

    def dump(self, t=None, depth=0):
        if t is None:
            t = self._tree
        mask, nodes = t.mask, t.children
        print "  " * depth, hex(mask), "=>"
        if type(nodes) is list:
            for i,d in enumerate(nodes):
                print "  " * depth, i, ":", d
        else:
            for i,k in enumerate(nodes.iterkeys()):
                print "  " * depth, i, ":", hex(k)
                self.dump(nodes[k], depth+1)

DECODER_TREE = DecoderTree()

class Decoder(object):
    def __init__(self, handler, spec, spec2=None, **kwargs):
        self._handler = handler
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

    def decode(self, hw1, hw2=0):
        attrs = {}
        for n,f in self._attrs.iteritems():
            attrs[n] = f(hw1)
#         if self._attrs2 is not None:
#             for n,f in self._attrs2.iteritems():
#                 attrs[n] = f(hw2)

        i = Instruction(hw1, hw2, attrs, self._handler)


        return i

    def __repr__(self):
        return "<Decoder@0x%x %x/%x %s %s>" % (id(self), self._mask, self._match, self._attrs)

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
                # Put a lambda to extract this named field from the instruction word into the d dict.
                name, size = f
                attrMask = (1 << size) - 1
                d[name] = lambda b,i=i+offset,attrMask=attrMask: (b >> i) & attrMask
                i += size
            else:
                raise ValueError("unexpected format element in spec: %s" % f)
        assert i == 16, "format was not exactly 16 bits"
        return mask, match, d

##
# @brief Decorator to build Decoder object from instruction format strings.
def instr(spec, spec2=None, **kwargs):
    def doit(fn):
        DECODER_TREE.add_decoder(Decoder(fn, spec, spec2, **kwargs))
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

        i += 1

    if ident:
        if not bitcount:
            bitcount = '1'
        result.append((ident, int(bitcount)))

    return result


