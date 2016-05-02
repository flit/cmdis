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

from .decoder import (Instruction, instr, DecodeError)
from .bitstring import (bitstring, bit0, bit1)
from .formatter import (RegisterOperand, ImmediateOperand, LabelOperand,
                        ShiftRotateOperand, BarrierOperand, MemoryAccessOperand)
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
        cpu.pc += self.size

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
        if hasattr(self, 'shift_n'):
            shift_n = self.shift_n
        else:
            shift_n = cpu.r[self.m][0:8].unsigned
        result, carry = Shift_C(cpu.r[self.n], self.type, shift_n, cpu.apsr.c)
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
    i.d = (DN % Rdn).unsigned
    i.n = i.d
    i.m = Rm.unsigned
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

@instr("lsls", ShiftOp, "000 stype=00 imm5(5) Rm(3) Rd(3)", type=SRType.SRType_LSL)
@instr("lsrs", ShiftOp, "000 stype=01 imm5(5) Rm(3) Rd(3)", type=SRType.SRType_LSR)
@instr("asrs", ShiftOp, "000 stype=10 imm5(5) Rm(3) Rd(3)", type=SRType.SRType_ASR)
def shift_imm_t1(i, stype, imm5, Rm, Rd):
    i.d = Rd.unsigned
    i.n = Rm.unsigned
    _, i.shift_n = DecodeImmShift(stype, imm5)
    i.setflags = SetFlags.NotInITBlock
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.n), ImmediateOperand(i.shift_n)]

# ------------------------------ Sign/unsigned extend instructions ------------------------------

class Extend(DataProcessing):
    def _eval(self, cpu):
        rotated = ROR(cpu.r[self.m], self.rotation)[0:self.width]
        if self.signed:
            result = rotated.sign_extend(32)
        else:
            result = rotated.zero_extend(32)
        cpu.r[self.d] = result
        cpu.pc += self.size

@instr("sxth", Extend, "1011 0010 00 Rm(3) Rd(3)", width=16, signed=True)
@instr("sxtb", Extend, "1011 0010 01 Rm(3) Rd(3)", width=8, signed=True)
@instr("uxth", Extend, "1011 0010 10 Rm(3) Rd(3)", width=16, signed=False)
@instr("uxtb", Extend, "1011 0010 11 Rm(3) Rd(3)", width=8, signed=False)
def extend(i, Rm, Rd):
    i.m = Rm.unsigned
    i.d = Rd.unsigned
    i.rotation = 0
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m)]

@instr("sxth.w", Extend, "11111 010 0 000 1111", "1111 Rd(4) 1 0 rotate(2) Rm(4)", width=16, signed=True)
@instr("sxtb.w", Extend, "11111 010 0 100 1111", "1111 Rd(4) 1 0 rotate(2) Rm(4)", width=8, signed=True)
@instr("uxth.w", Extend, "11111 010 0 001 1111", "1111 Rd(4) 1 0 rotate(2) Rm(4)", width=16, signed=False)
@instr("uxtb.w", Extend, "11111 010 0 101 1111", "1111 Rd(4) 1 0 rotate(2) Rm(4)", width=8, signed=False)
def extend2(i, Rm, rotate, Rd):
    i.m = Rm.unsigned
    i.d = Rd.unsigned
    i.rotation = (0, 8, 16, 24)[rotate.unsigned]
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m)]
    if i.rotation != 0:
        i.operands.append(ShiftRotateOperand(SRType.SRType_ROR, i.rotation))

# ------------------------------ Move instructions ------------------------------

class Move(DataProcessing):
    def __init__(self, mnemonic, word, is32bit):
        super(Move, self).__init__(mnemonic, word, is32bit)
        self.negate = False

    def _eval(self, cpu):
        if hasattr(self, 'm'):
            result = cpu.r[self.m]
            if self.m == 15: # pc
                self.setflags = SetFlags.Never
        else:
            result = self.imm32
        if self.negate:
            result = ~result
        cpu.r[self.d] = result
        self._set_flags(cpu, result, cpu.apsr.c, None)
        cpu.pc += self.size

@instr("mov", Move, "010001 10 D Rm(4) Rd(3)")
def mov0(i, D, Rm, Rd):
    i.m = Rm.unsigned
    i.d = (D % Rd).unsigned
    i.setflags = SetFlags.Never
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m)]

@instr("movs", Move, "000 00 00000 Rm(3) Rd(3)")
def mov0(i, Rm, Rd):
    i.m = Rm.unsigned
    i.d = Rd.unsigned
    i.setflags = SetFlags.Always
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m)]

@instr("mov", Move, "11101 01 0010 S 1111", "0 000 Rd(4) 0000 Rm(4)")
def mov_reg_t3(i, S, Rd, Rm):
    i._mnemonic += "s.w" if S else ".w"
    i.d = Rd.unsigned
    i.m = Rm.unsigned
    i.setflags = (SetFlags.Never, SetFlags.Always)[S.unsigned]
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m)]

@instr("movs", Move, "001 00 Rd(3) imm8(8)")
def mov1(i, Rd, imm8):
    i.d = Rd.unsigned
    i.setflags = SetFlags.NotInITBlock
    i.imm32 = imm8.zero_extend(32)
    i.operands = [RegisterOperand(i.d), ImmediateOperand(i.imm32.unsigned)]

# TODO test
@instr("mov", Move, "11110 im 0 0010 S 1111", "0 imm3(3) Rd(4) imm8(8)")
def mov2(i, im, S, imm3, Rd, imm8):
    i._mnemonic += "s.w" if S else ".w"
    i.d = Rd.unsigned
    i.setflags = (SetFlags.Never, SetFlags.Always)[S.unsigned]
    i.imm32, i.carry = ThumbExpandImm_C(im % imm3 % imm8, bit0) # TODO deal with carry_in
    i.operands = [RegisterOperand(i.d), ImmediateOperand(i.imm32.unsigned)]

# TODO test
@instr("movw", Move, "11110 im 10 0 1 0 0 imm4(4)", "0 imm3(3) Rd(4) imm8(8)")
def movw(i, im, imm4, imm3, Rd, imm8):
    i.d = Rd.unsigned
    i.setflags = SetFlags.Never
    i.imm32 = (imm4 % im % imm3 % imm8).zero_extend(32)
    i.operands = [RegisterOperand(i.d), ImmediateOperand(i.imm32.unsigned)]

# TODO test
@instr("mvns", Move, "010000 1111 Rm(3) Rd(3)", negate=True)
def mvn(i, Rm, Rd):
    i.d = Rd.unsigned
    i.m = Rm.unsigned
    i.setflags = SetFlags.NotInITBlock
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m)]

class ShiftedMoveNegate(DataProcessing):
    def _eval(self, cpu):
        shifted, carry = Shift_C(cpu.r[i.m], i.shift_t, i.shift_n, cpu.apsr.c)
        result = ~shifted
        cpu.r[self.d] = result
        self._set_flags(cpu, result, carry, None)
        cpu.pc += self.size

# TODO test
@instr("mvn", ShiftedMoveNegate, "11101 01 0011 S 1111", "0 imm3(3) Rd(4) imm2(2) type(2) Rm(4)")
def mvnw(i, S, imm3, Rd, imm2, type, Rm):
    i._mnemonic += "s.w" if S else ".w"
    i.d = Rd.unsigned
    i.m = Rm.unsigned
    i.setflags = (SetFlags.Never, SetFlags.Always)[S.unsigned]
    i.shift_t, i.shift_n = DecodeImmShift(type, imm3 % imm2)
    i.operands = [RegisterOperand(i.d), RegisterOperand(i.m), ShiftRotateOperand(i.shift_t, i.shift_n)]

# ------------------------------ Compare instructions ------------------------------

class Compare(Instruction):
    def __init__(self, mnemonic, word, is32bit):
        super(Compare, self).__init__(mnemonic, word, is32bit)
        self.negate = True

    def _eval(self, cpu):
        if hasattr(self, 'm'):
            shifted = cpu.r[self.m]
        else:
            shifted = self.imm32
        if self.negate:
            shifted = ~shifted
            carry_in = bit1
        else:
            carry_in = bit0
        result, carry, overflow = AddWithCarry(cpu.r[self.n], shifted, carry_in)
        cpu.apsr.n = result[31]
        cpu.apsr.z = result.is_zero_bit()
        cpu.apsr.c = carry
        cpu.apsr.v = overflow
        cpu.pc += self.size

@instr("cmp", Compare, "001 01 Rn(3) imm8(8)")
def cmp1(i, Rn, imm8):
    i.n = Rn.unsigned
    i.imm32 = imm8.zero_extend(32)
    i.operands = [RegisterOperand(i.n), ImmediateOperand(i.imm32.unsigned)]

# TODO test
@instr("cmp", Compare, "010000 1010 Rm(3) Rn(3)")
@instr("cmn", Compare, "010000 1011 Rm(3) Rn(3)", negate=False)
def cmp3(i, N, Rm, Rn):
    i.n = Rn.unsigned
    i.m = Rn.unsigned
    i.operands = [RegisterOperand(i.n), RegisterOperand(i.m)]

# TODO test
@instr("cmp", Compare, "010001 01 N Rm(4) Rn(3)")
def cmp4(i, N, Rm, Rn):
    i.n = (N % Rn).unsigned
    i.m = Rn.unsigned
    i.operands = [RegisterOperand(i.n), RegisterOperand(i.m)]

# TODO test
@instr("cmp.w", Compare, "11110 im 0 1101 1 Rn(4)", "0 imm3(3) 1111 imm8(8)")
@instr("cmn", Compare,   "11110 im 0 1000 1 Rn(4)", "0 imm3(3) 1111 imm8(8)", negate=False)
def cmp2(i, im, imm3, imm8):
    i.n = Rn.unsigned
    i.imm32 = ThumbExpandImm(im % imm3 % imm8)
    i.operands = [RegisterOperand(i.n), ImmediateOperand(i.imm32.unsigned)]

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
            next_instr = cpu.pc_for_instr + self.pc_delta
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
            cpu.pc += self.size

@instr("b", Branch, "1101 cond(4) imm8(8)")
def b_t1(i, cond, imm8):
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

# ------------------------------ Load instructions ------------------------------

class Load(Instruction):
    def __init__(self, mnemonic, word, is32bit):
        super(Load, self).__init__(mnemonic, word, is32bit)
        self.memsize = 32
        self.signed = False

    def _eval(self, cpu):
        if hasattr(self, 'imm32'):
            offset = self.imm32
        else:
            offset = Shift(cpu.r[self.m], self.shift_t, self.shift_n, cpu.apsr.c)
        offset_addr = (cpu.r[self.n] + offset) if self.add else (cpu.r[self.n] - offset)
        address = offset_addr if self.index else cpu.r[self.n]
        data = cpu.read_memory(address, self.memsize)
        if self.wback:
            cpu.r[self.n] = offset_addr
        if self.signed:
            data = data.sign_extend(32)
        else:
            data = data.zero_extend(32)
        cpu.r[self.t] = data
        cpu.pc += self.size

class Store(Instruction):
    def __init__(self, mnemonic, word, is32bit):
        super(Store, self).__init__(mnemonic, word, is32bit)
        self.memsize = 32
        self.signed = False

    def _eval(self, cpu):
        if hasattr(self, 'imm32'):
            offset = self.imm32
        else:
            offset = Shift(cpu.r[self.m], self.shift_t, self.shift_n, cpu.apsr.c)
        offset_addr = (cpu.r[self.n] + offset) if self.add else (cpu.r[self.n] - offset)
        address = offset_addr if self.index else cpu.r[self.n]
        cpu.write_memory(address, cpu.r[self.t][0:self.memsize], self.memsize)
        cpu.pc += self.size

@instr("str", Store,  "0101 000 Rm(3) Rn(3) Rt(3)", memsize=32)
@instr("strh", Store, "0101 001 Rm(3) Rn(3) Rt(3)", memsize=16)
@instr("strb", Store, "0101 010 Rm(3) Rn(3) Rt(3)", memsize=8)
@instr("ldrsb", Load, "0101 011 Rm(3) Rn(3) Rt(3)", memsize=8, signed=True)
@instr("ldr", Load,   "0101 100 Rm(3) Rn(3) Rt(3)", memsize=32)
@instr("ldrh", Load,  "0101 101 Rm(3) Rn(3) Rt(3)", memsize=16)
@instr("ldrb", Load,  "0101 110 Rm(3) Rn(3) Rt(3)", memsize=8)
@instr("ldrsh", Load, "0101 111 Rm(3) Rn(3) Rt(3)", memsize=16, signed=True)
def ldr_str_reg(i, Rm, Rn, Rt):
    i.t = Rt.unsigned
    i.n = Rn.unsigned
    i.m = Rm.unsigned
    i.index = True
    i.add = True
    i.wback = False
    i.shift_t = SRType.SRType_None
    i.shift_n = 0
    i.operands = [RegisterOperand(i.t), MemoryAccessOperand(RegisterOperand(i.n), RegisterOperand(i.m))]

@instr("ldrb.w", Load,  "11111 00 0 0 00 1 Rn(4)", "Rt(4) 0 00000 imm2(2) Rm(4)", memsize=8)
@instr("ldrh.w", Load,  "11111 00 0 0 01 1 Rn(4)", "Rt(4) 0 00000 imm2(2) Rm(4)", memsize=16)
@instr("ldr.w", Load,   "11111 00 0 0 10 1 Rn(4)", "Rt(4) 0 00000 imm2(2) Rm(4)", memsize=32)
@instr("ldrsb.w", Load, "11111 00 1 0 00 1 Rn(4)", "Rt(4) 0 00000 imm2(2) Rm(4)", memsize=8, signed=True)
@instr("ldrsh.w", Load, "11111 00 1 0 01 1 Rn(4)", "Rt(4) 0 00000 imm2(2) Rm(4)", memsize=16, signed=True)
@instr("strb.w", Store, "11111 00 0 0 00 0 Rn(4)", "Rt(4) 0 00000 imm2(2) Rm(4)", memsize=8)
@instr("strh.w", Store, "11111 00 0 0 01 0 Rn(4)", "Rt(4) 0 00000 imm2(2) Rm(4)", memsize=16)
@instr("str.w", Store,  "11111 00 0 0 10 0 Rn(4)", "Rt(4) 0 00000 imm2(2) Rm(4)", memsize=32)
def ldr_str_reg_t2(i, Rn, Rt, imm2, Rm):
    i.t = Rt.unsigned
    i.n = Rn.unsigned
    i.m = Rm.unsigned
    if i.n == 15:
        raise DecodeError()
    i.index = True
    i.add = True
    i.wback = False
    i.shift_t = SRType.SRType_LSL
    i.shift_n = imm2.unsigned
    i.operands = [RegisterOperand(i.t), MemoryAccessOperand(
        RegisterOperand(i.n), RegisterOperand(i.m), ShiftRotateOperand(i.shift_t, i.shift_n))]

@instr("str", Store,  "011 0 0 imm5(5) Rn(3) Rt(3)", memsize=32)
@instr("ldr", Load,   "011 0 1 imm5(5) Rn(3) Rt(3)", memsize=32)
@instr("strb", Store, "011 1 0 imm5(5) Rn(3) Rt(3)", memsize=8)
@instr("ldrb", Load,  "011 1 1 imm5(5) Rn(3) Rt(3)", memsize=8)
@instr("strh", Store, "100 0 0 imm5(5) Rn(3) Rt(3)", memsize=16)
@instr("ldrh", Load,  "100 0 1 imm5(5) Rn(3) Rt(3)", memsize=16)
def ldr_str_imm(i, imm5, Rn, Rt):
    i.t = Rt.unsigned
    i.n = Rn.unsigned
    if i.memsize == 32:
        imm5 %= '00'
    elif i.memsize == 16:
        imm5 %= '0'
    i.imm32 = imm5.zero_extend(32)
    i.index = True
    i.add = True
    i.wback = False
    i.operands = [RegisterOperand(i.t), MemoryAccessOperand(
        RegisterOperand(i.n), ImmediateOperand(i.imm32.unsigned, hideIfZero=True))]

class LoadLiteral(Load):
    def __init__(self, mnemonic, word, is32bit):
        super(LoadLiteral, self).__init__(mnemonic, word, is32bit)
        self.add = True

    def _eval(self, cpu):
        base = Align(cpu.pc_for_instr, 4)
        address = (base + self.imm32) if self.add else (base - self.imm32)
        data = cpu.read_memory(address, self.memsize)
        if self.signed:
            data = data.sign_extend(32)
        else:
            data = data.zero_extend(32)
        cpu.r[self.t] = data
        cpu.pc += self.size

@instr("ldr", LoadLiteral, "01001 Rt(3) imm8(8)", memsize=32)
def ldr_literal(i, Rt, imm8):
    i.t = Rt.unsigned
    i.imm32 = (imm8 % '00').zero_extend(32)
    i.operands = [RegisterOperand(i.t), MemoryAccessOperand(
        RegisterOperand(15), ImmediateOperand(i.imm32.unsigned))] # TODO label operand?

@instr("ldr.w", LoadLiteral,   "11111 00 0 U 10 1 1111", "Rt(4) imm12(12)", memsize=32)
@instr("ldrh.w", LoadLiteral,  "11111 00 0 U 01 1 1111", "Rt(4) imm12(12)", memsize=16)
@instr("ldrb.w", LoadLiteral,  "11111 00 0 U 00 1 1111", "Rt(4) imm12(12)", memsize=8)
@instr("ldrsh.w", LoadLiteral, "11111 00 1 U 01 1 1111", "Rt(4) imm12(12)", memsize=16, signed=True)
@instr("ldrsb.w", LoadLiteral, "11111 00 1 U 00 1 1111", "Rt(4) imm12(12)", memsize=8, signed=True)
def ldr_literal(i, U, Rt, imm12):
    i.t = Rt.unsigned
    if i.t == 15:
        raise DecodeError()
    i.imm32 = imm12.zero_extend(32)
    i.add = (U == '1')
    i.operands = [RegisterOperand(i.t), MemoryAccessOperand(
        RegisterOperand(15), ImmediateOperand(
        i.imm32.unsigned if i.add else -i.imm32.unsigned, hideIfZero=True))] # TODO label operand?

@instr("str", Store, "1001 0 Rt(3) imm8(8)", memsize=32)
@instr("ldr", Load,  "1001 1 Rt(3) imm8(8)", memsize=32)
def ldr_str_imm_t2(i, Rt, imm8):
    i.t = Rt.unsigned
    i.n = 13
    i.imm32 = (imm8 % '00').zero_extend(32)
    i.index = True
    i.add = True
    i.wback = False
    i.operands = [RegisterOperand(i.t), MemoryAccessOperand(
        RegisterOperand(13), ImmediateOperand(i.imm32.unsigned, hideIfZero=True))]

# ------------------------------ Nop-compatible hint instructions ------------------------------

@instr("nop", Instruction,      "1011 1111 0000 0000")
@instr("yield", Instruction,    "1011 1111 0001 0000")
@instr("wfe", Instruction,      "1011 1111 0010 0000")
@instr("wfi", Instruction,      "1011 1111 0011 0000")
@instr("sev", Instruction,      "1011 1111 0100 0000")
def nop(i):
    pass

# ------------------------------ Barrier instructions ------------------------------

@instr("dsb", Instruction, "11110 0 111 01 1 1111", "10 0 0 1111 0100 option(4)")
@instr("dmb", Instruction, "11110 0 111 01 1 1111", "10 0 0 1111 0101 option(4)")
@instr("isb", Instruction, "11110 0 111 01 1 1111", "10 0 0 1111 0110 option(4)")
def barrier(i, option):
    i.operands = [BarrierOperand(option.unsigned)]

