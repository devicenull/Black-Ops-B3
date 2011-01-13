#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
# Initial build 1/2/2011

__author__ = 'Bravo17'
__version__ = '1.1.1'

import b3, os, sys, time
import b3.plugin
import b3.cron
import shutil
import datetime
import math
import urllib
import urllib2
from b3 import functions
import b3.output
from array import array


#--------------------------------------------------------------------------------------------------


class ReadbologPlugin(b3.plugin.Plugin):
	_adminPlugin = None
	_cronTab = None
	_msg = None
	_fileName = None
	_rate = None
	_lastlinewritten=None
	_outputfile=None
	_bologurl=None
	_processing_file=None
	screen=None
	_firstread=None
	
	class DiffURLOpener(urllib2.HTTPRedirectHandler, urllib2.HTTPDefaultErrorHandler):
		"""Create sub-class in order to overide error 206.  This error means a
		partial file is being sent,
		which is ok in this case.  Do nothing with this error.
		"""
		def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
			pass
		# Ignore access denied as well
		def http_error_403(self, url, fp, errcode, errmsg, headers, data=None):
			pass


	def onStartup(self):

		self._adminPlugin = self.console.getPlugin('admin')
		

		if self.config.has_option('server','game_log'):
			# open log file
			game_log = self.config.get('server','game_log')
			self._outputfile = self.config.getpath('server', 'game_log')
			self.bot('Starting writing log to file %s', self._outputfile)
		
		if self.config.has_option('server','bo_logurl'):
			self._bologurl = self.config.get('server','bo_logurl')
			self.bot('Using Black Ops URL    : %s\n' % self._bologurl)
			

		req = urllib2.Request('http://logs.gameservers.com/timeout')
		f = urllib2.urlopen(req)
		self._rate = int(f.readlines()[0])
		f.close()
		
		#self._rate = 10
		if self._rate <= 10:
			self._rate=12
		
		self._cronTab = b3.cron.PluginCronTab(self, self.readbolog, '*/%s' % self._rate)
		self.console.cron + self._cronTab
		self._firstread = True


	def onLoadConfig(self):
		self._adminPlugin = self.console.getPlugin('admin')

		
	def readbolog(self):
		if not self._processing_file:
			print('Running Job')
			self._processing_file = True
			req = urllib2.Request(self._bologurl)
			req.headers['Range'] = 'bytes=-10000'
			req.add_header('User-Agent', 'readbolog/1.0 +tony556(at)comcast.net')
			DiffURLOpener = self.DiffURLOpener()
			httpopener = urllib2.build_opener(DiffURLOpener)
			httpFile = httpopener.open(req)
			
			#httpFile = urllib2.urlopen(req)
			log = httpFile.readlines()
			
			if self._firstread:
				self._lastlinewritten = ''
				i=-3
				while (self._lastlinewritten == ''):
					self._lastlinewritten = log[i]
					i=i-1

				logFile = open(self._outputfile,'a')
				logFile.write(self._lastlinewritten)
				self._firstread=False
				
			else:
			
				i=0

				while log[i] <> self._lastlinewritten:
					i=i+1

				i=i+1
				line = ''

				logFile = open(self._outputfile,'a')
				while i < (len(log)-2):
					line = log[i]
					logFile.write(line)
					i=i+1
					if line<>'':
						self._lastlinewritten = line

			logFile.close()
			httpFile.close()
			self._processing_file = False

if __name__ == '__main__':
    from b3.fake import fakeConsole
    from b3.fake import joe
    
    p = AdvPlugin(fakeConsole, '@b3/conf/plugin_adv.xml')
    p.onStartup()
    
    p.adv()
    print "-----------------------------"
    time.sleep(2)
    
    joe._maxLevel = 100
    joe.says('!advlist')
    time.sleep(2)
    joe.says('!advrem 0')
    time.sleep(2)
    joe.says('!advrate 1')
    time.sleep(5)
  