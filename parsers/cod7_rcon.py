#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Changelog :

# 2011/01/10 -1.1.0 - Bravo17
# * Support for cod7 rcon format added 
#
 
__author__ = 'Bravo17'
__version__ = '1.1.1'
 
import socket, sys, select, re, time, thread, threading, Queue
import b3
import b3.parsers.q3a_rcon

#--------------------------------------------------------------------------------------------------
class Cod7Rcon(b3.parsers.q3a_rcon.Rcon):
    rconsendstring = '\xff\xff\xff\xff\x00 "%s" %s\00'
    rconreplystring = '\xff\xff\xff\xff\x01print\n'
    def sendRcon(self, data, maxRetries=None, socketTimeout=None):
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
        if maxRetries is None:
            maxRetries = 2
            
        data = data.strip()
        self.console.verbose('RCON sending (%s:%s) %s', self.host[0], self.host[1], data)
        startTime = time.time()

        retries = 0
        while time.time() - startTime < 5:
            readables, writeables, errors = select.select([], [self.socket], [self.socket], socketTimeout)

            if len(errors) > 0:
                self.console.warning('RCON: %s', str(errors))
            elif len(writeables) > 0:
                try:
                    writeables[0].send(self.rconsendstring % (self.password, data))
 
                except Exception, msg:
                    self.console.warning('RCON: ERROR sending: %s', msg)
                else:
                    try:
                        data = self.readSocket(self.socket, socketTimeout=socketTimeout)
                        self.console.verbose2('RCON: Received %s' % data)
                        return data
                    except Exception, msg:
                        self.console.warning('RCON: ERROR reading: %s', msg)

                if re.match(r'^map(_rotate)?.*', data):
                    # do not retry map changes since they prevent the server from responding
                    self.console.verbose2('RCON: no retry for %s', data)
                    return ''
                    
            else:
                self.console.verbose('RCON: no writeable socket')

            time.sleep(0.05)

            retries += 1

            if retries >= maxRetries:
                self.console.error('RCON: too much tries. Abording (%s)', data.strip())
                break
            self.console.verbose('RCON: retry sending %s (%s/%s)...', data.strip(), retries, maxRetries)



        self.console.debug('RCON: Did not send any data')
        return ''

    def readNonBlocking(self, sock):
        sock.settimeout(2)

        startTime = time.time()

        data = ''
        while time.time() - startTime < 1:
            try:
                d = str(sock.recv(4096))
            except socket.error, detail:
                self.console.debug('RCON: ERROR reading: %s' % detail)
                break
            else:
                if d:
                    # remove rcon header
					data += d.replace(self.rconreplystring, '')
                elif len(data) > 0 and ord(data[-1:]) == 10:
                    break

        return data.strip()

    def readSocket(self, sock, size=4096, socketTimeout=None):
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
            
        data = ''

        readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
        
        if not len(readables):
            raise Exception('No readable socket')

        while len(readables):
            d = str(sock.recv(size))

            if d:
                # remove rcon header
				data += d.replace(self.rconreplystring, '')
				
            readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)

            if len(readables):
                self.console.verbose('RCON: More data to read in socket')

        return data.strip()

