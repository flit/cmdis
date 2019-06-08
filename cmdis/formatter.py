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

from .utilities import bytes_to_le16
from .registers import CORE_REGISTER_NAMES
from .helpers import SRType

class Operand(object):
    def format(self, formatter):
        raise NotImplemented()

class RegisterOperand(Operand):
    def __init__(self, reg, wback=False):
        self._reg = reg
        self._wback = wback

    def format(self, formatter):
        result = CORE_REGISTER_NAMES[self._reg]
        if self._wback:
            result += "!"
        return result

class ReglistOperand(Operand):
    def __init__(self, reglist):
        self._reglist = reglist

    def format(self, formatter):
        regs = []
        startRange = -1
        endRange = -1

        def add_reg_range(regs):
            if startRange != -1:
                if startRange == endRange:
                    regs.append(CORE_REGISTER_NAMES[startRange])
                else:
                    startReg = CORE_REGISTER_NAMES[startRange]
                    endReg = CORE_REGISTER_NAMES[endRange]
                    regs.append("%s-%s" % (startReg, endReg))

        for n, b in enumerate(self._reglist):
            if b:
                if startRange == -1:
                    startRange = n
                endRange = n
            else:
                add_reg_range(regs)
                startRange = -1
                endRange = -1
        add_reg_range(regs)

        return '{' + ','.join(regs) + '}'

class ImmediateOperand(Operand):
    def __init__(self, imm, hideIfZero=False):
        self._imm = imm
        self._hideIfZero = hideIfZero

    def format(self, formatter):
        if self._imm == 0 and self._hideIfZero:
            return None

        if self._imm > 9:
            comment = "0x%x" % (self._imm)
            formatter.add_comment(comment)

        return "#%d" % self._imm

class LabelOperand(Operand):
    def __init__(self, offset):
        self._offset = offset

    def format(self, formatter):
        # Add a comment with the absolute address of the label.
        comment = "0x%x" % (formatter.instruction.address + 4 + self._offset)
        formatter.add_comment(comment)

        return ".%+d" % (self._offset + 4)

class ShiftRotateOperand(Operand):
    OP_NAMES = ["None",
                "LSL",
                "LSR",
                "ASR",
                "ROR",
                "RRX",]

    def __init__(self, type, amount):
        self._type = type
        self._amount = amount

    def format(self, formatter):
        if self._type == SRType.SRType_None:
            return None
        return "%s #%d" % (self.OP_NAMES[self._type.value], self._amount)

class BarrierOperand(Operand):
    def __init__(self, option):
        self._option = option

    def format(self, formatter):
        if self._option == 0b1111:
            return "sy"
        else:
            return "#%d" % self._option

class MemoryAccessOperand(Operand):
    def __init__(self, *args, **kwargs):
        self._operands = args
        self._wback = kwargs.get("wback", False)

    def format(self, formatter):
        formattedOperands = []
        for o in self._operands:
            formatted = o.format(formatter)
            if formatted is not None:
                formattedOperands.append(formatted)

        result = "[" + ", ".join(formattedOperands) + "]"
        if self._wback:
            result += "!"
        return result

class CpsOperand(Operand):
    def __init__(self, affectPri, affectFault):
        self._affectPri = affectPri
        self._affectFault = affectFault

    def format(self, formatter):
        result = ""
        if self._affectPri:
            result += "i"
        if self._affectFault:
            result += "f"
        return result

class SpecialRegisterOperand(Operand):
    def __init__(self, spec, mask=-1):
        self._spec = spec
        self._mask = mask

    def format(self, formatter):
        result = ""
        upper = self._spec[3:8]
        lower = self._spec[0:3]
        if upper == '00000':
            if lower == '000':
                result = "APSR"
            elif lower == '001':
                result = "IAPSR"
            elif lower == '010':
                result = "EAPSR"
            elif lower == '011':
                result = "XPSR"
            elif lower == '101':
                result = "IPSR"
            elif lower == '110':
                result = "EPSR"
            elif lower == '111':
                result = "IEPSR"
            if lower < 4 and self._mask != -1:
                if self._mask == '10':
                    result += '_nzcvq'
                elif self._mask == '01':
                    result += '_g'
                elif self._mask == '11':
                    result += '_nzcvqg'
        elif upper == '00001':
            if lower == '000':
                result = "MSP"
            elif lower == '001':
                result = "PSP"
        elif upper == '00010':
            if lower == '000':
                result = "PRIMASK"
            elif lower == '001':
                result = "BASEPRI"
            elif lower == '010':
                result = "BASEPRI_MAX"
            elif lower == '011':
                result = "FAULTMASK"
            elif lower == '100':
                result = "CONTROL"
        return result

class Formatter(object):
    def __init__(self, cpu):
        self.instruction = None
        self.cpu = cpu
        self._comments = []

    def format(self, instruction):
        self.instruction = instruction
        self._comments = []

        b = instruction.bytes
        hw1 = bytes_to_le16(b, 0)
        byteString = "%04x" % hw1
        if len(b) == 4:
            hw2 = bytes_to_le16(b, 2)
            byteString += " %04x" % hw2

        result = "{0:<12} {1:<8}".format(byteString, self.instruction.mnemonic)

        formattedOperands = []
        for o in self.instruction.operands:
            formatted = o.format(self)
            if formatted is not None:
                formattedOperands.append(formatted)

        result += ", ".join(formattedOperands)

        if self._comments:
            result = "{0:<36} ; {1}".format(result, " ".join(self._comments))

        self.instruction = None
        return result

    def add_comment(self, comment):
        self._comments.append(comment)



