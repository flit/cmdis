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

import six
from functools import total_ordering
import collections

##
# @brief Variable length bit string.
@total_ordering
class bitstring(object):
    __slots__ = ("_width", "_value", "_mask")

    def __init__(self, val=None, width=None):
        # Set value based on type and default width.
        if val is None:
            self._width = 0
            self._value = 0
        elif isinstance(val, bitstring):
            self._width = val._width
            self._value = val._value
        elif isinstance(val, six.integer_types):
            # Integer.
            self._width = 64 if (val > (1 << 32)) else 32
            self._value = val
        elif isinstance(val, six.string_types):
            # String.
            self._width = len(val)
            self._value = int(val, base=2)
        elif isinstance(val, collections.Sequence):
            # Iterable.
            # TODO support iterables of '0','1' as well as ints
            self._width = len(val)
            self._value = reduce(lambda x,y:(x << 1) | y, val)
        else:
            raise TypeError("value type is not supported")

        # Set custom width.
        if width is not None:
            self._width = width

        # Mask value.
        self._mask = (1 << self._width) - 1
        self._value &= self._mask

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val & self._mask

    @property
    def signed(self):
        if self._width < 2:
            return 0

        w1 = self._width - 1
        s = (self._value >> w1) & 1
        if s:
            v = -(self.invert().value & ((1 << w1) - 1)) - 1
        else:
            v = self._value & ((1 << w1) - 1)
        return v

    @property
    def unsigned(self):
        return self._value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, val):
        self._width = val
        self._mask = (1 << self._width) - 1
        self._value &= self._mask

    @property
    def mask(self):
        return self._mask

    @property
    def binary_string(self):
        s = ''
        for i in range(self._width):
            s = str((self._value >> i) & 1) + s
        return s

    def __repr__(self):
        return "%d'b%s" % (self._width, self.binary_string)

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        if isinstance(other, six.integer_types):
            # If other is negative then compare the signed value of this bitstring.
            if other < 0:
                return self.signed == other
            else:
                return self._value == other
        elif isinstance(other, six.string_types):
            return self.__eq__(bitstring(other))
        else:
            return (self._width == other._width and self._value == other._value) \
                if isinstance(other, bitstring) else NotImplemented

    def __lt__(self, other):
        if isinstance(other, six.integer_types):
            # If other is negative then compare the signed value of this bitstring.
            if other < 0:
                return self.signed < other
            else:
                return self._value < other
        elif isinstance(other, six.string_types):
            return self.__lt__(bitstring(other))
        else:
            return ((self._width < other._width) if (self._value == other._value) \
                else (self._value < other._value)) \
                if isinstance(other, bitstring) else NotImplemented

    def __nonzero__(self):
        return self._value != 0

    def __len__(self):
        return self._width

    def __int__(self):
        return self._value

    def __index__(self):
        return self._value

    def get_bit(self, bitpos):
        if bitpos < 0:
            bitpos = self._width + bitpos
        return bitstring((self._value >> bitpos) & 1, 1)

    def get_bit_value(self, bitpos):
        return (self._value >> bitpos) & 1

    def bit_count(self):
        count = 0
        v = self._value
        while v != 0:
            count += v & 1
            v >>= 1
        return count

    def is_zero(self):
        return self._value == 0

    def is_ones(self):
        return self.bit_count() == self._width

    def is_zero_bit(self):
        return bitstring('1') if self.is_zero() else bitstring('0')

    def is_ones_bit(self):
        return bitstring('1') if self.is_ones() else bitstring('0')

    def lowest_set_bit(self):
        v = self._value
        for n in range(0, self._width):
            if v & 1:
                return n
            v >>= 1
        return self._width

    def highest_set_bit(self):
        for n in range(self._width - 1, -1, -1):
            if (self._value >> n) & 1:
                return n
        return -1

    def __getitem__(self, key):
        if isinstance(key, slice):
            start, stop, step = key.indices(self._width)
            i = start
            result = bitstring()
            while (i < stop) if (step > 0) else (i > stop):
                result = self.get_bit(i) + result
                i += step
            return result
        elif isinstance(key, six.integer_types):
            return self.get_bit(key)
        else:
            raise TypeError("index must be an integer or slice")

    def __setitem__(self, key, value):
        if not isinstance(key, six.integer_types):
            raise TypeError("index must be an integer")
        if key >= self._width:
            raise IndexError("index out of range")
        if isinstance(value, bitstring):
            if value.width != 1:
                raise ValueError("cannot assign multibit bitstring to single bit")
            value = value.unsigned
        elif not isinstance(value, six.integer_types):
            raise TypeError("index must be an integer")
        if key < 0:
            key = self._width + key
        mask = self._mask & ~(1 << key)
        self._value = (self._value & mask) | ((value & 1) << key)

    def __delitem__(self, key):
        return NotImplemented

    def __iter__(self):
        for i in range(self._width):
            yield (self._value >> i) & 1

    def __reversed__(self):
        return NotImplemented

    def set(self, other):
        if not isinstance(other, bitstring):
            raise TypeError("argument is not a bitstring")
        self._width = other._width
        self._mask = other._mask
        self._value = other._value

    def reverse(self):
        self.set(reversed(self))

    def sign_extend(self, width):
        if width < self._width:
            raise ValueError("new width is smaller than current")
        elif width == self._width:
            return self
        w1 = self._width - 1
        s = (self._value >> w1) & 1
        d = width - self._width
        b = bitstring([s] * d)
        return b % self

    def zero_extend(self, width):
        if width < self._width:
            raise ValueError("new width is smaller than current")
        elif width == self._width:
            return self
        return bitstring(self, width)

    def invert(self):
        return bitstring(self._mask & ~self._value, self._width)

    def __add__(self, other):
        b = bitstring(self)
        b.__iadd__(other)
        return b

    def __sub__(self, other):
        b = bitstring(self)
        b.__isub__(other)
        return b

    def __mul__(self, other):
        b = bitstring(self)
        b.__imul__(other)
        return b

    def __floordiv__(self, other):
        b = bitstring(self)
        b.__ifloordiv__(other)
        return b

    def __mod__(self, other):
        b = bitstring(self)
        b.__imod__(other)
        return b

    def __lshift__(self, other):
        if isinstance(other, six.integer_types):
            w = self._width + other
            v = self._value << other
            return bitstring(v, w)
        else:
            return NotImplemented

    def __rshift__(self, other):
        if isinstance(other, six.integer_types):
            if self._width - other < 0:
                return bitstring()
            w = self._width - other
            v = self._value >> other
            return bitstring(v, w)
        else:
            return NotImplemented

    def __and__(self, other):
        if isinstance(other, bitstring):
            width = max(self._width, other._width)
            other = other._value
            width = self._width
        else:
            width = self._width
        if isinstance(other, six.string_types):
            other = bitstring(other).unsigned
        return bitstring(self._value & other, width)

    def __xor__(self, other):
        if isinstance(other, bitstring):
            width = max(self._width, other._width)
            other = other._value
        else:
            width = self._width
        if isinstance(other, six.string_types):
            other = bitstring(other).unsigned
        return bitstring(self._value ^ other, width)

    def __or__(self, other):
        if isinstance(other, bitstring):
            width = max(self._width, other._width)
            other = other._value
        else:
            width = self._width
        if isinstance(other, six.string_types):
            other = bitstring(other).unsigned
        return bitstring(self._value | other, width)

    def __iadd__(self, other):
        if isinstance(other, bitstring):
            value = other.unsigned
        elif isinstance(other, six.integer_types):
            value = other
        elif isinstance(other, six.string_types):
            value = bitstring(other).unsigned
        else:
            return NotImplemented
        self._value += value
        self._value &= self._mask
        return self

    def __isub__(self, other):
        if isinstance(other, bitstring):
            value = other.unsigned
        elif isinstance(other, six.integer_types):
            value = other
        elif isinstance(other, six.string_types):
            value = bitstring(other).unsigned
        else:
            return NotImplemented
        self._value -= value
        self._value &= self._mask
        return self

    def __imul__(self, other):
        if isinstance(other, bitstring):
            value = other.unsigned
        elif isinstance(other, six.integer_types):
            value = other
        elif isinstance(other, six.string_types):
            value = bitstring(other).unsigned
        else:
            return NotImplemented
        self._value *= value
        self._value &= self._mask
        return self

    def __ifloordiv__(self, other):
        if isinstance(other, bitstring):
            value = other.unsigned
        elif isinstance(other, six.integer_types):
            value = other
        elif isinstance(other, six.string_types):
            value = bitstring(other).unsigned
        else:
            return NotImplemented
        self._value //= value
        self._value &= self._mask
        return self

    def __imod__(self, other):
        if isinstance(other, bitstring):
            self._width += other._width
            self._mask = (1 << self._width) - 1
            self._value = (self._value << other._width) | other._value
            return self
        elif isinstance(other, six.string_types):
            return self.__imod__(bitstring(other))
        elif isinstance(other, six.integer_types):
            if other not in (0, 1):
                raise ValueError("cannot add integer to a bitstring that is neither 0 or 1")
            return self.__imod__(bitstring(other, 1))
        elif isinstance(other, collections.Sequence):
            return self.__imod__(bitstring(other))
        else:
            return NotImplemented

    def __ilshift__(self, other):
        self.set(self.__lshift__(other))
        return self

    def __irshift__(self, other):
        self.set(self.__rshift__(other))
        return self

    def __iand__(self, other):
        self.set(self.__and__(other))
        return self

    def __ixor__(self, other):
        self.set(self.__xor__(other))
        return self

    def __ior__(self, other):
        self.set(self.__or__(other))
        return self

    def __invert__(self):
        return self.invert()

    def __hex__(self):
        return "%d'h%0*x" % (self._width, (self._width + 3) // 4, self._value)

bit0 = bitstring('0')
bit1 = bitstring('1')

def zeros(count):
    return bitstring('0' * count)

def ones(count):
    return bitstring('1' * count)




