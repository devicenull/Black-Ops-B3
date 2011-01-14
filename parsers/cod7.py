# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
# 1/13/2010 - 1.1.0
#    * Copied from COD parser  1.4.15
#    * _regPlayer edited to allow for negative qports
#    * removed suicides from TK action and added log entries for TK/Suicides
#    * added no of players check to see if in pre-match and ignore TK's etc if so
#    * added creation of layer list in log since no pb list

__author__  = 'ThorN, xlr8or'
__version__ = '1.4.15'

import b3.parsers.q3a
import b3.parsers.cod
import re, string, threading
import b3
import b3.events
import b3.parsers.punkbuster
import b3.parsers.cod7_rcon

class Cod7Parser(b3.parsers.cod.CodParser):
    gameName = 'cod7'
    OutputClass = b3.parsers.cod7_rcon.Cod7Rcon

    _logSync = 3 # Value for unbuffered game logging (append mode) 

    _num_players = 0 # Needed to see whether in pre-match to control TK warnings



    #num score ping guid   name            lastmsg address               qport rate
    #--- ----- ---- ------ --------------- ------- --------------------- ----- -----
    #2     0   29 465030 <-{^4AS^7}-^3ThorN^7->^7       50 68.63.6.62:-32085      6597  5000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9-]+)\s+(?P<rate>[0-9]+)$', re.I)


		
    # kill
    def OnK(self, action, data, match=None):
        # check if in pre-match
        if self._num_players < 6:
            return None

        victim = self.getClient(victim=match)
        if not victim:
            self.debug('No victim')
            self.OnJ(action, data, match)
            return None

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.debug('No attacker')
            return None

        attacker.team = self.getTeam(match.group('ateam'))
        attacker.name = match.group('aname')
        victim.team = self.getTeam(match.group('team'))
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_KILL

        if attacker.cid == victim.cid or attacker.cid == '-1':
            self.verbose2('Suicide Detected')
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            self.verbose2('Teamkill Detected')
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

    # damage
    def OnD(self, action, data, match=None):
        # check if in pre-match
        if self._num_players < 6:
            return None

        victim = self.getClient(victim=match)
        if not victim:
            self.debug('No victim - attempt join')
            self.OnJ(action, data, match)
            return None

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.debug('No attacker')
            return None

        attacker.team = self.getTeam(match.group('ateam'))
        attacker.name = match.group('aname')
        victim.team = self.getTeam(match.group('team'))
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_DAMAGE
        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_DAMAGE_SELF
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_DAMAGE_TEAM

        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)




    def getPlayerList(self, maxRetries=None):
        if self.PunkBuster:
            return self.PunkBuster.getPlayerList()
        else:
            data = self.write('status', maxRetries=maxRetries)
            if not data:
                return {}
            self._num_players = 0
            players = {}
            for line in data.split('\n')[3:]:
                self.verbose('getPlayerList() = Line: %s' % line)
                m = re.match(self._regPlayer, line.strip())

                if m:
                    d = m.groupdict()
                    d['pbid'] = None
                    players[str(m.group('slot'))] = d
                    self._num_players = self._num_players + 1
                elif '------' not in line and 'map: ' not in line and 'num score ping' not in line:
                    self.verbose('getPlayerList() = Line did not match format: %s' % line)

        return players


#--LogLineFormats---------------------------------------------------------------

#===============================================================================
# 
# *** CoD:
# Join:               J;160913;10;PlayerName
# Quit:               Q;160913;10;PlayerName
# Damage by world:    D;160913;14;axis;PlayerName;;-1;world;;none;6;MOD_FALLING;none
# Damage by opponent: D;160913;19;allies;PlayerName;248102;10;axis;OpponentName;mp44_mp;27;MOD_PISTOL_BULLET;right_foot
# Kill:               K;160913;4;axis;PlayerName;578287;0;axis;OpponentName;kar98k_mp;180;MOD_HEAD_SHOT;head
# Weapon/ammo pickup: Weapon;160913;8;PlayerName;m1garand_mp
# Action:             A;160913;16;axis;PlayerName;htf_scored
# Say to All:         say;160913;8;PlayerName;^Ubye
# Say to Team:        sayteam;160913;8;PlayerName;^Ulol
# Private message:    tell;160913;12;PlayerName1;1322833;8;PlayerName2;what message?
# Winners:            W;axis;160913;PlayerName1;258015;PlayerName2
# Losers:             L;allies;160913;PlayerName1;763816;PlayerName2
# 
# ExitLevel:          ExitLevel: executed
# Shutdown Engine:    ShutdownGame:
# Seperator:          ------------------------------------------------------------
# InitGame:           InitGame: \_Admin\xlr8or\_b3\B3 v1.2.1b [posix]\_Email\admin@xlr8or.com\_Host\[SNT]
#                    \_Location\Twente University - The Netherlands\_URL\http://games.snt.utwente.nl/\fs_game\xlr1.7
#                    \g_antilag\1\g_gametype\tdm\gamename\Call of Duty 2\mapname\mp_toujane\protocol\115
#                    \scr_friendlyfire\3\scr_killcam\1\shortversion\1.0\sv_allowAnonymous\0\sv_floodProtect\1
#                    \sv_hostname\^5[SNT] #3 ^7Tactical Gaming ^9(^7B3^9) (^1v1.0^9)\sv_maxclients\24\sv_maxPing\220
#                    \sv_maxRate\20000\sv_minPing\0\sv_privateClients\8\sv_pure\1\sv_voice\1
# 
# 
# *** CoD5 specific lines:
# JoinTeam:           JT;283895439;17;axis;PlayerName;
#                    AD;564;allies;580090035;6;axis;PlayerName;stg44_mp;30;MOD_RIFLE_BULLET;right_arm_lower
#===============================================================================
