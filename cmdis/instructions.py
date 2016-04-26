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
from .helpers import *
from collections import namedtuple
from enum import Enum
import operator

class SetFlags(Enum):
    Always = 1
    Never = 2
    NotInITBlock = 3

# ------------------------------ Data processing instructions ------------------------------

class DataProcessing(Instruction):
    def __init__(self, mnemonic, word, is32bit):
        super(DataProcessing, self).__init__(mnemonic, word, is32bit)
        self.setflags = SetFlags.Never

    def _set_flags(self, cpu, result, carry, overflow):
        if self.setflags == SetFlags.Always:
            setflags = True
        elif self.setflags == SetFlags.Never:
            setflags = False
        elif self.setflags == SetFlags.NotInITBlock:
            setflags = not cpu.in_it_block

        if setflags:
            cpu.apsr.n = result[31]
            cpu.apsr.z = result.is_zero_bit()
            cpu.apsr.c = carry
            if overflow is not None:
                cpu.apsr.v = overflow

    def _eval(self, cpu):
        cpu.pc = cpu.pc.unsigned + self.size

class AddSub(DataProcessing):
    def __init__(self, mnemonic, word, is32bit):
        super(AddSub, self).__init__(mnemonic, word, is32bit)
        self.use_carry = False
        self.sub = False

    def _eval(self, cpu):
        if self.sub:
            result, carry, overflow = AddWithCarry(cpu.r[self.n],
                ~(self.imm32 if hasattr(self, 'imm32') else cpu.r[self.m]),
                cpu.apsr.c if self.use_carry else bit1)
        else:
            result, carry, overflow = AddWithCarry(cpu.r[self.n],
                self.imm32 if hasattr(self, 'imm32') else cpu.r[self.m],
                cpu.apsr.c if self.use_carry else bit0)
        cpu.r[self.d] = result
        self._set_flags(cpu, result, carry, overflow)
        super(AddSub, self)._eval(cpu)

class BitOp(DataProcessing):
    def _eval(self, cpu):
        result = self.op(cpu.r[self.n], cpu.r[self.m])
        cpu.r[self.d] = result
        self._set_flags(cpu, result, cpu.apsr.c, None)
        super(BitOp, self)._eval(cpu)

class BitClear(DataProcessing):
    def _eval(self, cpu):
        result = cpu.r[self.n] & ~cpu.r[self.m]
        cpu.r[self.d] = result
        self._set_flags(cpu, result, cpu.apsr.c, None)
        super(BitClear, self)._eval(cpu)

class ShiftOp(DataProcessing):
    def _eval(self, cpu):
        result, carry = Shift_C(cpu.r[self.n], self.type, cpu.r[self.m][0:8].unsigned, cpu.apsr.c)
        cpu.r[self.d] = result
        self._set_flags(cpu, result, carry, None)
        super(ShiftOp, self)._eval(cpu)

@instr("ands", BitOp,        "010000 0000 Rm(3) Rdn(3)", op=operator.and_)
@instr("eors", BitOp,        "010000 0001 Rm(3) Rdn(3)", op=operator.xor)
@instr("lsls", ShiftOp,      "010000 0010 Rm(3) Rdn(3)", type=SRType.SRType_LSL)
@instr("lsrs", ShiftOp,      "010000 0011 Rm(3) Rdn(3)", type=SRType.SRType_LSR)
@instr("asrs", ShiftOp,      "010000 0100 Rm(3) Rdn(3)", type=SRType.SRType_ASR)
@instr("adcs", AddSub,       "010000 0101 Rm(3) Rdn(3)", use_carry=True)
@instr("sbcs", AddSub,       "010000 0110 Rm(3) Rdn(3)", sub=True, use_carry=True)
@instr("rors", ShiftOp,      "010000 0111 Rm(3) Rdn(3)", type=SRType.SRType_ROR)
@instr("orrs", BitOp,        "010000 1100 Rm(3) Rdn(3)", op=operator.or_)
@instr("bics", BitClear,     "010000 1110 Rm(3) Rdn(3)")
def adc(i, Rm, Rdn):
    i.d = Rdn.unsigned
    i.n = Rdn.unsigned
    i.m = Rm.unsigned
    i.setflags = SetFlags.NotInITBlock
#     shift_t, shift_n = SRType_LSL, 0

    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m)]

@instr("adds", AddSub, "000 11 1 0 imm3(3) Rn(3) Rd(3)")
@instr("subs", AddSub, "000 11 1 1 imm3(3) Rn(3) Rd(3)", sub=True)
def add_imm_t1(i, imm3, Rn, Rd):
    i.d = Rd.unsigned
    i.n = Rn.unsigned
    i.setflags = SetFlags.NotInITBlock
    i.imm32 = imm3.zero_extend(32)

    i.operands = [RegisterOperand(i.d), RegisterOperand(i.n), ImmediateOperand(i.imm32)]

@instr("adds", AddSub, "001 10 Rdn(3) imm8(8)")
@instr("subs", AddSub, "001 11 Rdn(3) imm8(8)", sub=True)
def add_imm_t2(i, Rdn, imm8):
    i.d = Rdn.unsigned
    i.n = Rdn.unsigned
    i.setflags = SetFlags.NotInITBlock
    i.imm32 = imm8.zero_extend(32)

    i.operands = [RegisterOperand(i.d), ImmediateOperand(i.imm32)]

@instr("adds", AddSub, "000 11 0 0 Rm(3) Rn(3) Rd(3)")
@instr("subs", AddSub, "000 11 0 1 Rm(3) Rn(3) Rd(3)", sub=True)
def add_reg_t1(i, Rm, Rn, Rd):
    i.d = Rd.unsigned
    i.n = Rn.unsigned
    i.m = Rm.unsigned
    i.setflags = SetFlags.NotInITBlock
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.n), RegisterOperand(i.m)]

@instr("add", AddSub, "010001 00 DN Rm(4) Rdn(3)")
def add_reg_t2(i, DN, Rm, Rdn):
    # if (DN:Rdn) == '1101' || Rm == '1101' then SEE ADD (SP plus register);
    i.d = (DN % Rdn).unsigned
    i.n = i.d
    i.m = Rm.unsigned
    # if n == 15 && m == 15 then UNPREDICTABLE;
    # if d == 15 && InITBlock() && !LastInITBlock() then UNPREDICTABLE;
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m)]

@instr("add", AddSub, "1010 1 Rd(3) imm8(8)")
def add_sp_plus_imm_t1(i, Rd, imm8):
    i.d = Rd.unsigned
    i.n = 13
    i.imm32 = (imm8 % '00').zero_extend(32)
    i.operands = [RegisterOperand(i.d), RegisterOperand(13), ImmediateOperand(i.imm32.unsigned)]

@instr("add", AddSub, "1011 0000 0 imm7(7)")
@instr("sub", AddSub, "1011 0000 1 imm7(7)", sub=True)
def add_sp_plus_imm_t2(i, imm7):
    i.d = 13
    i.n = 13
    i.imm32 = (imm7 % '00').zero_extend(32)
    i.operands = [RegisterOperand(13), ImmediateOperand(i.imm32.unsigned)]

# ------------------------------ Branch instructions ------------------------------

ConditionInfo = namedtuple('ConditionInfo', 'mnemonic expr')

CONDITIONS = {
    0b0000 : ConditionInfo('eq', lambda apsr: apsr.z == 1), # Equal
    0b0001 : ConditionInfo('ne', lambda apsr: apsr.z == 0), # Not equal
    0b0010 : ConditionInfo('cs', lambda apsr: apsr.c == 1), # Carry set
    0b0011 : ConditionInfo('cc', lambda apsr: apsr.c == 0), # Carry clear
    0b0100 : ConditionInfo('mi', lambda apsr: apsr.n == 1), # Minus, negative
    0b0101 : ConditionInfo('pl', lambda apsr: apsr.n == 0), # Plus, positive or zero
    0b0110 : ConditionInfo('vs', lambda apsr: apsr.v == 1), # Overflow
    0b0111 : ConditionInfo('vc', lambda apsr: apsr.v == 0), # No overflow
    0b1000 : ConditionInfo('hi', lambda apsr: apsr.c == 1 and apsr.z == 0), # Unsigned higher
    0b1001 : ConditionInfo('ls', lambda apsr: apsr.c == 0 or apsr.z == 1), # Unsigned lower or same
    0b1010 : ConditionInfo('ge', lambda apsr: apsr.n == apsr.v), # Signed greater than or equal
    0b1011 : ConditionInfo('lt', lambda apsr: apsr.n != apsr.v), # Signed less than
    0b1100 : ConditionInfo('gt', lambda apsr: apsr.z == 0 and apsr.n == apsr.v), # Signed greater than
    0b1101 : ConditionInfo('le', lambda apsr: apsr.z == 1 or apsr.n != apsr.v), # Signed less than or equal
    0b1110 : ConditionInfo('', lambda apsr: True),   # never encoded
    0b1111 : ConditionInfo('', lambda apsr: True),   # always (al)
    }

class Branch(Instruction):
    def __init__(self, mnemonic, word, is32bit):
        super(Branch, self).__init__(mnemonic, word, is32bit)
        self.with_link = False
        self.cond = CONDITIONS[0b1111]
        self.pc_delta = 0

    def _eval(self, cpu):
        # TODO deal with pc + 4
        if self.cond.expr(cpu.apsr):
            # TODO bl: next_inst_addr = pc
            # TODO blx: next_inst_addr = pc - 2
            next_instr = cpu.pc + 4 + self.pc_delta
            if self.with_link:
                cpu.lr = next_instr | 1

            if hasattr(self, 'm'):
                # Branch to register
                target = bitstring(cpu.r[self.m])
                target[0] = 0 # clear T bit
                cpu.pc = target
            else:
                # Branch to immediate offset
                cpu.pc = next_instr + self.imm32
        else:
            cpu.pc = cpu.pc + self.size

@instr("b", Branch, "1101 cond(4) imm8(8)")
def b_t1(i, cond, imm8):
    # if cond == '1110' then UNDEFINED;
    # if cond == '1111' then SEE SVC;
    i.cond = CONDITIONS[cond.unsigned]
    i._mnemonic = 'b' + CONDITIONS[cond.unsigned].mnemonic
    i.imm32 = (imm8 % '0').sign_extend(32)
    i.operands = [LabelOperand(i.imm32.signed)]

@instr("b", Branch, "11100 imm11(11)")
def b_t2(i, imm11):
    i.cond = bitstring('1111')
    i.imm32 = (imm11 % '0').sign_extend(32)
    i.operands = [LabelOperand(i.imm32.signed)]

@instr("bl", Branch, "11110 S imm10(10)", "11 J1 1 J2 imm11(11)")
def bl_t1(i, S, imm10, J1, J2, imm11):
    I1 = ~(J1 ^ S)
    I2 = ~(J2 ^ S)
    i.imm32 = (S % I1 % I2 % imm10 % imm11 % '0').sign_extend(32)
    i.with_link = True
    i.operands = [LabelOperand(i.imm32.signed)]

@instr("blx", Branch, "010001 11 1 Rm(4) 000")
def blx_t1(i, Rm):
    i.m = Rm.unsigned
    # if m == 15 then UNPREDICTABLE;
    i.with_link = True
    i.pc_delta = -2
    i.operands = [RegisterOperand(i.m)]

@instr("bx", Branch, "010001 11 0 Rm(4) 000")
def bx_t1(i, Rm):
    i.m = Rm.unsigned
    i.operands = [RegisterOperand(i.m)]





