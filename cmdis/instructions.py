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

from .decoder import instr

@instr("010000 0101 Rm(3) Rdn(3)", mnemonic="adc")
def ADC(Rm, Rdn):
    pass
#     d = UInt(Rdn)
#     n = UInt(Rdn)
#     m = UInt(Rm)
#     setflags = !InITBlock()
#     shift_t, shift_n = SRType_LSL, 0
#
#     if ConditionPassed():
#         shifted = Shift(R[m], shift_t, shift_n, APSR.C)
#         (result, carry, overflow) = AddWithCarry(R[n], shifted, APSR.C)
#         R[d = result
#         if setflags:
#             APSR.N = result[31]
#             APSR.Z = IsZeroBit(result)
#             APSR.C = carry
#             APSR.V = overflow

@instr("000 11 1 0 imm3(3) Rn(3) Rd(3)", mnemonic="add")
def ADD_imm_T1(imm3, Rn, Rd):
    pass
#     d = UInt(Rd)
#     n = UInt(Rn)
#     setflags = !InITBlock()
#     imm32 = ZeroExtend(imm3, 32)
#
#     if ConditionPassed():
#         (result, carry, overflow) = AddWithCarry(R[n], imm32, 0)
#         R[d] = result
#         if setflags:
#             APSR.N = result[31]
#             APSR.Z = IsZeroBit(result)
#             APSR.C = carry
#             APSR.V = overflow

@instr("001 10 Rdn(3) imm8(8)", mnemonic="add")
def ADD_imm_T2(Rdn, imm8):
    pass

@instr("000 11 0 0 Rm(3) Rn(3) Rd(3)", mnemonic="add")
def ADD_reg_T1(Rm, Rn, Rd):
    pass

@instr("010001 00 DN Rm(4) Rdn(3)", mnemonic="add")
def ADD_reg_T2(Rm, Rn, Rd):
    pass

@instr("1010 1 Rd(3) imm8(8)", mnemonic="add")
def ADD_sp_plus_imm_T1(Rn, imm8):
    pass

@instr("1011 0000 0 imm7(7)", mnemonic="add")
def ADD_sp_plus_imm_T2(imm7):
    pass



@instr("1101 cond(4) imm8(8)", mnemonic="b")
def B_T1(imm7):
    pass

@instr("11100 imm11(11)", mnemonic="b")
def B_T2(imm7):
    pass

@instr("11110 S imm10(10)", "11 J1 1 J2 imm11(11)", mnemonic="bl")
def BL_T1(imm7):
    pass

@instr("010001 11 1 Rm(4) 000", mnemonic="blx")
def BLX_T1(imm7):
    pass





