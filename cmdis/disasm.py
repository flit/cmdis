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

from . import instructions
from .decoder import (DECODER_TREE, UndefinedInstructionError)

decoder = DECODER_TREE
decoder.build()

class Disassembler(object):
    def __init__(self):
        pass

    def disasm(self, data, address=0):
        length = len(data)
        endAddress = address + length
        offset = 0
        while address < endAddress:
            # Decode the next instruction.
            try:
                i = decoder.decode(data[offset:], address)
            except UndefinedInstructionError:
                # Ignore the undefined error if it's the last few bytes.
                if endAddress - address < 4:
                    return
                raise

            # Return this instruction to the caller.
            yield i

            # Update address based on instruction length.
            address += i.size
            offset += i.size



