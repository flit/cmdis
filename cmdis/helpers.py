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

from .utilities import wmask
from .bitstring import (bitstring, bit0, bit1, zeros)
from enum import Enum

class SRType(Enum):
    SRType_None = 0
    SRType_LSL = 1
    SRType_LSR = 2
    SRType_ASR = 3
    SRType_ROR = 4
    SRType_RRX = 5

##
# @return (bits(N), bit, bit)
def AddWithCarry(x, y, carry_in):
    assert x.width == y.width
    unsigned_sum = x.unsigned + y.unsigned + carry_in.unsigned
    signed_sum = x.signed + y.signed + carry_in.unsigned
    result = bitstring(unsigned_sum, x.width) # same value as signed_sum<N-1:0>
    carry_out = bit0 if result.unsigned == unsigned_sum else bit1
    overflow = bit0 if result.signed == signed_sum else bit1
    return (result, carry_out, overflow)

def LSL_C(x, shift):
    assert shift > 0
    ext_x = x % zeros(shift)
    result = ext_x[0:x.width]
    carry_out = ext_x[x.width]
    return result, carry_out

def LSL(x, shift):
    return x << shift

def LSR_C(x, shift):
    assert shift > 0
    ext_x = x.zero_extend(shift + x.width)
    result = ext_x[shift:shift+x.width]
    carry_out = ext_x[shift-1]
    return result, carry_out

def LSR(x, shift):
    return x >> shift

def ASR_C(x, shift):
    assert shift > 0
    ext_x = x.sign_extend(shift + x.width)
    result = ext_x[shift:shift+x.width]
    carry_out = ext_x[shift-1]
    return result, carry_out

def ASR(x, shift):
    assert shift >= 0
    if shift == 0:
        result = c
    else:
        result, _ = ASR_C(x, shift)
    return result

def ROR_C(x, shift):
    assert shift != 0
    m = shift % x.width
    result = LSR(x, m) | (LSL(x, x.width - m))
    carry_out = result[x.width-1]
    return result, carry_out

def ROR(x, shift):
    if shift == 0:
        result = x
    else:
        result, _ = ROR_C(x, shift)
    return result

def RRX_C(x, carry_in):
    result = carry_in % x[1:x.width]
    carry_out = x[0]
    return result, carry_out

def RRX(x, carry_in):
    result, _ = RRX_C(x, carry_in)
    return result

def Shift_C(value, type, amount, carry_in):
    assert not (type == SRType.SRType_RRX and amount != 1)

    if amount == 0:
        result, carry_out = value, carry_in
    else:
        if type == SRType.SRType_LSL:
            result, carry_out = LSL_C(value, amount)
        elif type == SRType.SRType_LSR:
            result, carry_out = LSR_C(value, amount)
        elif type == SRType.SRType_ASR:
            result, carry_out = ASR_C(value, amount)
        elif type == SRType.SRType_ROR:
            result, carry_out = ROR_C(value, amount)
        elif type == SRType.SRType_RRX:
            result, carry_out = RRX_C(value, carry_in)

    return result, carry_out

def Shift(value, type, amount, carry_in):
    result, _ = Shift_C(value, type, amount , carry_in)
    return result

def DecodeImmShift(type, imm5):
    if type == '00':
        shift_t = SRType.SRType_LSL
        shift_n = imm5.unsigned
    elif type == '01':
        shift_t = SRType.SRType_LSR
        shift_n = 32 if imm5 == '00000' else imm5.unsigned
    elif type == '10':
        shift_t = SRType.SRType_ASR
        shift_n = 32 if imm5 == '00000' else imm5.unsigned
    elif type == '11':
        if imm5 == '00000':
            shift_t = SRType.SRType_RRX
            shift_n = 1
        else:
            shift_t = SRType.SRType_ROR
            shift_n = imm5.unsigned
    else:
        raise ValueError("unknown type value %s" % type)
    return shift_t, shift_n

# @param carry_in Either passed through unchanged or not used. Does not affect result imm32.
def ThumbExpandImm_C(imm12, carry_in):
    if imm12[10:12] == '00':
        imm12_8 = imm12[8:10]
        imm12_0 = imm12[0:8]
        if imm12_8 == '00':
            imm32 = imm12_0.zero_extend(32)
        elif imm12_8 == '01':
            imm32 = bitstring('00000000') % imm12_0 % bitstring('00000000') % imm12_0
        elif imm12_8 == '10':
            imm32 = imm12_0 % bitstring('00000000') % imm12_0 % bitstring('00000000')
        elif imm12_8 == '11':
            imm32 = imm12_0 % imm12_0 % imm12_0 % imm12_0
        carry_out = carry_in
    else:
        unrotated_value = (bit1 % imm12[0:7]).zero_extend(32)
        imm32, carry_out = ROR_C(unrotated_value, imm12[7:12].unsigned)
    return imm32, carry_out

def ThumbExpandImm(imm12):
    # Carry in param to this call is ignored.
    imm32, _ = ThumbExpandImm_C(imm12, bit0)
    return imm32



