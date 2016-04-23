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

from .utilities import bytes_to_le16

class Operand(object):
    def format(self, formatter):
        raise NotImplemented()

class RegisterOperand(Operand):
    def __init__(self, reg):
        self._reg = reg

    def format(self, formatter):
        return "r%d" % self._reg

class ImmediateOperand(Operand):
    def __init__(self, imm):
        self._imm = imm

    def format(self, formatter):
        return "#%d" % self._imm

class LabelOperand(Operand):
    def __init__(self, offset):
        self._offset = offset

    def format(self, formatter):
        # Add a comment with the absolute address of the label.
        # TODO use instr address instead of pc
        comment = "0x%08x" % (formatter.cpu.pc.unsigned + self._offset)
        formatter.add_comment(comment)

        return "*%+d" % self._offset

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
            formattedOperands.append(o.format(self))

        result += ", ".join(formattedOperands)

        if self._comments:
            result += "    ; " + " ".join(self._comments)

        self.instruction = None
        return result

    def add_comment(self, comment):
        self._comments.append(comment)



