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

## @brief Compute the hamming weight, or number of 1s, of the argument.
def hamming_weight(v):
    weight = 0
    while v != 0:
        weight += v & 1
        v >>= 1
    return weight

## @brief Convert two bytes to an unsigned halfword.
#
# @param data Iterable of ints where each is 0 <= x < 256.
def bytes_to_le16(data, offset=0):
    return data[offset] | (data[offset+1] << 8)

## @brief Convert four bytes to an unsigned halfword.
#
# @param data Iterable of ints where each is 0 <= x < 256.
def bytes_to_le32(data, offset=0):
    return data[offset] | (data[offset+1] << 8) | (data[offset+2] << 16) | (data[offset+3] << 24)

## @brief Convert an unsigned halfword to a bytearray.
#
# @param data Integer.
def le16_to_bytes(value, offset=0):
    return bytearray((value >> (i * 8)) & 0xff for i in range(2))

## @brief Convert an unsigned halfword to a bytearray.
#
# @param data Integer.
def le32_to_bytes(value, offset=0):
    return bytearray((value >> (i * 8)) & 0xff for i in range(4))

def byteListToU32leList(data):
    """Convert a list of bytes to a list of 32-bit integers (little endian)"""
    res = []
    for i in range(len(data) / 4):
        res.append(data[i * 4 + 0] |
                   data[i * 4 + 1] << 8 |
                   data[i * 4 + 2] << 16 |
                   data[i * 4 + 3] << 24)
    return res

def u32leListToByteList(data):
    """Convert a word array into a byte array"""
    res = []
    for x in data:
        res.append((x >> 0) & 0xff)
        res.append((x >> 8) & 0xff)
        res.append((x >> 16) & 0xff)
        res.append((x >> 24) & 0xff)
    return res

def u16leListToByteList(data):
    """Convert a halfword array into a byte array"""
    byteData = []
    for h in data:
        byteData.extend([h & 0xff, (h >> 8) & 0xff])
    return byteData

def byteListToU16leList(byteData):
    """Convert a byte array into a halfword array"""
    data = []
    for i in range(0, len(byteData), 2):
        data.append(byteData[i] | (byteData[i + 1] << 8))
    return data

def u32BEToFloat32BE(data):
    """Convert a 32-bit int to an IEEE754 float"""
    d = struct.pack(">I", data)
    return struct.unpack(">f", d)[0]

def float32beToU32be(data):
    """Convert an IEEE754 float to a 32-bit int"""
    d = struct.pack(">f", data)
    return struct.unpack(">I", d)[0]

## @brief Returns an integer with all bits set up to but not including bit n.
#
# If n == 4, then 0xf will be returned.
def wmask(n):
    return (1 << n) - 1

## @brief Returns a mask with specified bit ranges set.
#
# An integer mask is generated based on the bits and bit ranges specified by the
# arguments. Any number of arguments can be provided. Each argument may be either
# a 2-tuple of integers, a list of integers, or an individual integer. The result
# is the combination of masks produced by the arguments.
#
# - 2-tuple: The tuple is a bit range with the first element being the MSB and the
#       second element the LSB. All bits from LSB up to and included MSB are set.
# - list: Each bit position specified by the list elements is set.
# - int: The specified bit position is set.
#
# @return An integer mask value computed from the logical OR'ing of masks generated
#   by each argument.
#
# Example:
# @code
#   >>> hex(bitmask((23,17),1))
#   0xfe0002
#   >>> hex(bitmask([4,0,2],(31,24))
#   0xff000015
# @endcode
def bitmask(*args):
    mask = 0

    for a in args:
        if type(a) is tuple:
            for b in range(a[1], a[0]+1):
                mask |= 1 << b
        elif type(a) is list:
            for b in a:
                mask |= 1 << b
        elif type(a) is int:
            mask |= 1 << a

    return mask

## @brief Return the 32-bit inverted value of the argument.
def invert32(value):
    return 0xffffffff & ~value

## @brief Extract a value from a bitfield.
def bfx(value, msb, lsb=None):
    lsb = lsb or msb
    mask = bitmask((msb, lsb))
    return (value & mask) >> lsb

## @brief Change a bitfield value.
def bfi(value, field, msb, lsb=None):
    lsb = lsb or msb
    mask = bitmask((msb, lsb))
    value &= ~mask
    value |= (field << lsb) & mask
    return value
