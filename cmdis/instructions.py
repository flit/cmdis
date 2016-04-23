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

from .decoder import (Instruction, instr)
from .bitstring import (bitstring, bit0, bit1)
from .formatter import (RegisterOperand, ImmediateOperand, LabelOperand)
from . import helpers

class Add(Instruction):
    def __init__(self, mnemonic, word, is32bit, attrs=None):
        super(Add, self).__init__(mnemonic, word, is32bit, attrs)
        self.add_carry = False
        self.setflags = False

    def _eval(self, cpu):
        result, carry, overflow = helpers.AddWithCarry(cpu.r[self.n],
            self.imm32 if hasattr(self, 'imm32') else cpu.r[self.m],
            cpu.apsr.c if self.add_carry else bit0)
        cpu.r[self.d] = result
        if self.setflags:
            cpu.apsr.n = result[31]
            cpu.apsr.z = result.is_zero_bit()
            cpu.apsr.c = carry
            cpu.apsr.v = overflow
        cpu.pc = cpu.pc.unsigned + self.size

@instr("adcs", Add, "010000 0101 Rm(3) Rdn(3)")
def adc(i, Rm, Rdn):
    i.d = Rdn.unsigned
    i.n = Rdn.unsigned
    i.m = Rm.unsigned
    i.setflags = True #!InITBlock()
    i.add_carry = True
#     shift_t, shift_n = SRType_LSL, 0

    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m)]

@instr("adds", Add, "000 11 1 0 imm3(3) Rn(3) Rd(3)")
def add_imm_t1(i, imm3, Rn, Rd):
    i.d = Rd.unsigned
    i.n = Rn.unsigned
    i.setflags = True #!InITBlock()
    i.imm32 = imm3.zero_extend(32)

    i.operands = [RegisterOperand(i.d), ImmediateOperand(i.imm32)]

@instr("add", Add, "001 10 Rdn(3) imm8(8)")
def add_imm_t2(i, Rdn, imm8):
    i.d = Rdn.unsigned
    i.n = Rdn.unsigned
    i.setflags = True #!InITBlock()
    i.imm32 = imm8.zero_extend(32)

    i.operands = [RegisterOperand(i.d), ImmediateOperand(i.imm32)]

@instr("add", Add, "000 11 0 0 Rm(3) Rn(3) Rd(3)")
def add_reg_t1(i, Rm, Rn, Rd):
    pass

@instr("add", Add, "010001 00 DN Rm(4) Rdn(3)")
def add_reg_t2(i, Rm, Rn, Rd):
    pass

@instr("add", Add, "1010 1 Rd(3) imm8(8)")
def add_sp_plus_imm_t1(i, Rn, imm8):
    pass

@instr("add", Add, "1011 0000 0 imm7(7)")
def add_sp_plus_imm_t2(i, imm7):
    pass


class Branch(Instruction):
    def __init__(self, mnemonic, word, is32bit, attrs=None):
        super(Branch, self).__init__(mnemonic, word, is32bit, attrs)
        self.with_link = False

    def _eval(self, cpu):
        next_instr = cpu.pc
        if self.with_link:
            cpu.lr = next_instr | 1
        cpu.pc = next_instr.unsigned + self.imm32.signed

@instr("b", Branch, "1101 cond(4) imm8(8)")
def b_t1(i, cond, imm8):
    pass

@instr("b", Branch, "11100 imm11(11)")
def b_t2(i, imm11):
    pass

@instr("bl", Branch, "11110 S imm10(10)", "11 J1 1 J2 imm11(11)")
def bl_t1(i, S, imm10, J1, J2, imm11):
    I1 = ~(J1 ^ S)
    I2 = ~(J2 ^ S)
    i.imm32 = (S + I1 + I2+ imm10 + imm11 + '0').sign_extend(32)
    i.with_link = True

    i.operands = [LabelOperand(i.imm32.signed)]

@instr("blx", Branch, "010001 11 1 Rm(4) 000")
def blx_t1(i, imm7):
    pass





