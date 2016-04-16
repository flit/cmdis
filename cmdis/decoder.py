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

import string

# Grammar:
#
# start         => field*
#
# field         => bit | value
#
# bit           => '0' | '1'
#
# value         => ident ( '(' intlit ')' )?
#
# ident         => /[a-zA-Z][a-zA-Z0-9]*/
#
# intlit        => /[0-9]+/
#
def parse_spec(spec):
    result = []
    i = 0
    state = 0
    ident = ''
    bitcount = ''
    expectingBitcount = False
    while i < len(spec):
        c = spec[i]

        # Default state.
        if state == 0:
            if c in ('0', '1'):
                if ident:
                    result.append((ident, 1))
                    ident = ''
                result.append(int(c))
                expectingBitcount = False
            elif c in string.ascii_letters:
                if ident:
                    result.append((ident, 1))
                    ident = ''
                ident = c
                state = 1
            elif c == '(' and expectingBitcount:
                state = 2
            elif c in string.whitespace:
                pass
            else:
                raise ValueError("unexpected character '%s' at position %d" % (c, i))
        # Ident state.
        elif state == 1:
            if c == '(':
                state = 2
            elif c not in string.ascii_letters + string.digits:
                # Switch to default state and back up.
                state = 0
                i -= 1
                expectingBitcount = True
            else:
                ident += c
        # Enter bitcount state.
        elif state == 2:
            if c in string.digits:
                bitcount = c
                state = 3
            elif c == ')':
                bitcount = '1'
                state = 0
            elif c in string.whitespace:
                pass
            else:
                raise ValueError("unexpected character '%s' at position %d" % (c, i))
        # Bitcount state.
        elif state == 3:
            if c == ')':
                result.append((ident, int(bitcount)))
                ident = ''
                bitcount = ''
                state = 0
            elif c not in string.digits:
                state = 4
            else:
                bitcount += c
        # Close bitcount state.
        elif state == 4:
            if c == ')':
                result.append((ident, int(bitcount)))
                ident = ''
                bitcount = ''
                state = 0
            elif c in string.whitespace:
                pass
            else:
                raise ValueError("unexpected character '%s' at position %d" % (c, i))

        i += 1

    if ident:
        if not bitcount:
            bitcount = '1'
        result.append((ident, int(bitcount)))

    return result


