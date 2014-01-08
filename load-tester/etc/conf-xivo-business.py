# -*- coding: utf-8 -*-

# Copyright (C) 2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from __future__ import unicode_literals

## global configuration

sipp_remote_host = '10.101.0.227'

sipp_local_ip = '10.101.0.241'
sipp_call_rate = 1.0
sipp_rate_period_in_ms = 1000
#sipp_max_simult_calls = 3
#sipp_nb_of_calls_before_exit = 4
#sipp_enable_trace_calldebug = True
#sipp_enable_trace_err = True
#sipp_enable_trace_shortmsg = True
sipp_enable_trace_stat = True


## global scenarios configuration

answer_bind_port = 5060
call_bind_port = 5064

calling_line = {
    'username': 'loadtester',
    'password': 'loadtester',
}

pause = {
    'distribution': 'fixed',
    'value': 5000,
}
#pause = {
#    'distribution': 'uniform',
#    'min': 3000,
#    'max': 7000,
#}
#pause = {
#    'distribution': 'normal',
#    'mean': 5000,
#    'stdev': 1000,
#}

answer_ring_time = {'distribution': 'uniform', 'min': 500, 'max': 1000}
answer_talk_time = {'distribution': 'uniform', 'min': 10 * 1000, 'max': 30 * 1000}
call_talk_time = {'distribution': 'uniform', 'min': 10 * 1000, 'max': 40 * 1000}

#rtp = None
#rtp = 'test3s-gsm.pcap'
rtp = '/home/trafgen/xivo-loadtest/load-tester/pcap-audio/test3s-gsm.pcap'
#rtp = 'silence600s-gsm.pcap'


## scenarios configuration

scenarios.answer_then_hangup = dict(
    bind_port = answer_bind_port,
    ring_time = answer_ring_time,
    talk_time = answer_talk_time,
    rtp = rtp,
)

scenarios.answer_then_wait = dict(
    bind_port = answer_bind_port,
    ring_time = answer_ring_time,
    rtp = rtp,
)

scenarios.call_then_hangup = dict(
    bind_port = call_bind_port,
    calling_line = calling_line,
    called_extens = ['61000'],
    talk_time = call_talk_time,
    rtp = rtp,
    sipp_call_rate = 1.0,
    sipp_rate_period_in_ms = 4000,
)
