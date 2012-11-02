#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright (C) 2012  Avencall
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

import sys
import argparse
import ConfigParser
import time
from xivo_ws import XivoServer
from xivo_ws import User
from xivo_ws import UserLine
from xivo_ws import Agent
from xivo_ws import Queue
from xivo_ws import Incall
from xivo_ws import QueueDestination

def main():
    parsed_args = _parse_args()

    section = parsed_args.section
    if section == None:
        print '[Error] - section to use not defined'
        sys.exit(1)

    dataset = ManageDataset(section)
    dataset.create_dataset()

def _parse_args():
    parser = _new_argument_parser()
    return parser.parse_args()

def _new_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--section', type=str,
                        help='Section to use from dataset.cfg')
    return parser

class ManageDataset(object):
    def __init__(self, section):
        config = ConfigParser.RawConfigParser()
        config.read('dataset.cfg')
        self.host = config.get(section, 'host')
        self.user = config.get(section, 'user')
        self.secret = config.get(section, 'secret')
 
        self.nb_users = config.getint(section, 'nb_users')
        self.users_first_line = config.getint(section, 'users_first_line')
 
        self.nb_agents = config.getint(section, 'nb_agents')
        self.agents_first_id = config.getint(section, 'agents_first_id')
 
        self.available_agents_cnf = config.getint(section, 'available_agents_cnf')
        self.nb_agent_by_queue = config.getint(section, 'nb_agent_by_queue')
        self.queue_member_overlap = config.getint(section, 'queue_member_overlap')
        self.queues_first_context = config.getint(section, 'queues_first_context')
 
        self.incalls_first_line = config.getint(section, 'incalls_first_line')

        self._initiate_connection()

    def create_dataset(self):
        user_list = self._get_user_list()
        agent_list = self._get_agent_list()
        queue_list = self._get_queue_list()

        user_start_line = self._get_user_start_line(user_list)
        if user_start_line > self.users_first_line:
            nb_user_to_create = user_start_line - ( self.users_first_line + self.nb_users )
        else:
            nb_user_to_create = self.nb_users
        if nb_user_to_create > 0:
            self._add_users(user_start_line)
            self._wait_for_commit()

        if self.nb_agents > 0:
            agent_start_id = self._get_agent_start_id(agent_list)
            self._add_agents(agent_start_id, user_list)
            self._wait_for_commit()
            available_agents = self.nb_users
        else:
            available_agents = self.available_agents_cnf

        agent_id = self._get_agent_id(agent_list, available_agents)
        nb_queue_add = self._get_nb_queue_add(available_agents, queue_list)
        queue_start_nb = self._get_queue_start_nb(queue_list)

        if ( nb_queue_add > ( queue_start_nb - self.queues_first_context )):
            self._add_queues(nb_queue_add, queue_start_nb, agent_id)

        # Recall of _get_queue_list() once queues are created
        queue_list = self._get_queue_list()
        queue_list_nb_id = self._get_queue_list_nb_id(queue_list)
        nb_incalls_add = self._get_nb_incalls_add(queue_list_nb_id)
        if nb_incalls_add > 0:
            self._add_incall(queue_list_nb_id, nb_incalls_add)
 
    def _initiate_connection(self):
        try:
            self.xs = XivoServer(self.host, self.user, self.secret)
        except:
            print '[Error] - No connection to XiVO'
            sys.exit(1)

    def _get_user_last_line(self, user_list):
        try:
            last_id = max([int(user.lastname) for user in user_list if user.lastname != ''])
            return last_id
        except:
            print '[INFO] - No other loadtest users found, beginning with %s' % self.users_first_line
            return 0

    def _get_user_list(self):
        return self.xs.users.list()

    def _get_user_start_line(self, user_list):
        user_last_line = self._get_user_last_line(user_list)
        if len(user_list) > 0 and user_last_line != 0:
            users_start_line = ( 1 + user_last_line )
        else:
            users_start_line = self.users_first_line
        return users_start_line

    def _get_agent_list(self):
        return self.xs.agents.list()

    def _get_agent_start_id(self, agent_list):
        if len(agent_list) > 0:
            agent_start_id = ( 1 + int(sorted([agent.number for agent in agent_list])[-1]) )
        else:
            agent_start_id = self.agents_first_id
        return agent_start_id

    def _add_users(self, user_start_line):
        print 'Add users ..'
        users = []
        for offset in range(user_start_line, self.users_first_line + self.nb_users):
            user = User(firstname=u'User', lastname=u'' + str(offset))
            user.line = UserLine(context=u'default', number=offset)
            users.append(user)
        print 'Import %d users...' % len(users)
        self.xs.users.import_(users)

    def _add_agents(self, agent_start_id, user_list):
        user_id = sorted([user.id for user in user_list])[-self.nb_agents:]
 
        agent_end_id = self.agents_first_id + self.nb_agents
        if agent_start_id < agent_end_id:
            print 'Add agents ..'
            for offset in range(agent_start_id, agent_end_id):
                agent = Agent(firstname=u'Agent',
                          #lastname=str( agent_start_id - agents_first_id + offset ),
                          lastname=str(offset),
                          number=offset,
                          context=u'default',
                          users=[ user_id[offset - agent_start_id] ])
                self.xs.agents.add(agent)
                print 'Agent %s number %s added on user %s' % (agent.lastname, offset, agent.users)
 
    def _get_agent_id(self, agent_list, available_agents):
        return sorted([agent.id for agent in agent_list])[-available_agents:]

    def _get_nb_queue_add(self, available_agents, queue_list):
        return ( available_agents / ( self.nb_agent_by_queue - self.queue_member_overlap ) - len(queue_list) )

    def _get_queue_list(self):
        return self.xs.queues.list()

    def _get_queue_start_nb(self, queue_list):
        if len(queue_list) > 0:
            queue_start_nb = int(queue_list[-1].number) + 1
        else:
            queue_start_nb = self.queues_first_context
        return queue_start_nb
 
    def _add_queues(self, nb_queues_add, queue_start_nb, agent_id):
        for offset in range(queue_start_nb, queue_start_nb + nb_queues_add):
            first_agent_index = ( offset - self.queues_first_context ) * ( self.nb_agent_by_queue - self.queue_member_overlap ) 
            print 'Add queue..'
            queue = Queue(name=u'queue%s' % offset,
                          display_name=u'Queue %s' % offset,
                          number=offset,
                          context=u'default',
                          ring_strategy=u'rrmemory',
                          autopause=False,
                          agents=agent_id[first_agent_index:first_agent_index + self.nb_agent_by_queue])

            self.xs.queues.add(queue)
            print 'Queue %s number added with %s agents' % (offset, queue.agents)
 
    def _get_queue_list_nb_id(self, queue_list):
        return sorted((queue.number, queue.id) for queue in queue_list)

    def _get_incall_list(self):
        return self.xs.incalls.list()

    def _get_nb_incalls_add(self, queue_list_nb_id):
        return len(queue_list_nb_id) - len(self._get_incall_list())

    def _add_incall(self, queue_list_nb_id, nb_incalls_add):
        print 'Add Incalls ..'
        # TODO : Boucle FOR qui commence au N ieme element donne par nb_incalls_add
        for queue_nb, queue_id in queue_list_nb_id[-nb_incalls_add]:
            incall = Incall()
            incall.number = self.incalls_first_line + int(queue_nb) - self.queues_first_context
            incall.context = 'from-extern'
            incall.destination = QueueDestination(queue_id)
            print 'Adding incall %s %s...' % (incall.number, incall.destination)
            self.xs.incalls.add(incall)

    def _wait_for_commit(self):
        time.sleep(2)

if __name__ == "__main__":
    main()
