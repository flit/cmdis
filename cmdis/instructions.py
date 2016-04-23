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
from .utilities import wmask
from .bitstring import (bitstring, bit0, bit1)
from . import helpers

@instr("adcs", "010000 0101 Rm(3) Rdn(3)")
def ADC(cpu, Rm, Rdn):
    d = Rdn.unsigned
    n = Rdn.unsigned
    m = Rm.unsigned
    setflags = True #!InITBlock()
#     shift_t, shift_n = SRType_LSL, 0

#     if ConditionPassed():
#     shifted = Shift(cpu.r[m], shift_t, shift_n, cpu.apsr.c)
    result, carry, overflow = helpers.AddWithCarry(cpu.r[n], cpu.r[m], cpu.apsr.c)
    cpu.r[d] = result
    if setflags:
        cpu.apsr.n = result[31]
        cpu.apsr.z = result.is_zero_bit()
        cpu.apsr.c = carry
        cpu.apsr.v = overflow

    cpu.pc = cpu.pc.unsigned + 2

@instr("adds", "000 11 1 0 imm3(3) Rn(3) Rd(3)")
def ADD_imm_T1(cpu, imm3, Rn, Rd):
    d = Rd.unsigned
    n = Rn.unsigned
    setflags = True #!InITBlock()
    imm32 = imm3.zero_extend(32)

#     if ConditionPassed():
    (result, carry, overflow) = helpers.AddWithCarry(cpu.r[n], imm32, bit0)
    cpu.r[d] = result
    if setflags:
        cpu.apsr.n = result[31]
        cpu.apsr.z = result.is_zero_bit()
        cpu.apsr.c = carry
        cpu.apsr.v = overflow

    cpu.pc = cpu.pc.unsigned + 2

@instr("add", "001 10 Rdn(3) imm8(8)")
def ADD_imm_T2(cpu, Rdn, imm8):
    d = Rdn.unsigned
    n = Rdn.unsigned
    setflags = True #!InITBlock()
    imm32 = imm8.zero_extend(32)

#     if ConditionPassed():
    (result, carry, overflow) = helpers.AddWithCarry(cpu.r[n], imm32, bit0)
    cpu.r[d] = result
    if setflags:
        cpu.apsr.n = result[31]
        cpu.apsr.z = result.is_zero_bit()
        cpu.apsr.c = carry
        cpu.apsr.v = overflow

    cpu.pc = cpu.pc.unsigned + 2

@instr("add", "000 11 0 0 Rm(3) Rn(3) Rd(3)")
def ADD_reg_T1(cpu, Rm, Rn, Rd):
    pass

@instr("add", "010001 00 DN Rm(4) Rdn(3)")
def ADD_reg_T2(cpu, Rm, Rn, Rd):
    pass

@instr("add", "1010 1 Rd(3) imm8(8)")
def ADD_sp_plus_imm_T1(cpu, Rn, imm8):
    pass

@instr("add", "1011 0000 0 imm7(7)")
def ADD_sp_plus_imm_T2(cpu, imm7):
    pass



@instr("b", "1101 cond(4) imm8(8)")
def B_T1(cpu, cond, imm8):
    pass

@instr("b", "11100 imm11(11)")
def B_T2(cpu, imm11):
    pass

@instr("bl", "11110 S imm10(10)", "11 J1 1 J2 imm11(11)")
def BL_T1(cpu, S, imm10, J1, J2, imm11):
    I1 = ~(J1 ^ S)
    I2 = ~(J2 ^ S)
    imm32 = (S + I1 + I2+ imm10 + imm11 + '0').sign_extend(32)
    next_instr = cpu.pc
    cpu.lr = next_instr | 1
    cpu.pc = next_instr.unsigned + imm32.signed

@instr("blx", "010001 11 1 Rm(4) 000")
def BLX_T1(cpu, imm7):
    pass





