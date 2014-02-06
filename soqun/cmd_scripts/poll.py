"""
@TODO short description.

@TODO long description if needed.

"""
import ConfigParser
import json

import logging
import datetime
import re
import hipchat
import os
import sys
import time
from jinja2 import Environment, PackageLoader
import requests

__copyright__ = """
MIT Something
"""

__author__ = 'Tadeusz Kozak'
__email__ = 'ted@addlive.com'
__date__ = '06.02.2014 20:07'


# ?order=desc&sort=activity&site=stackoverflow
_SEARCH_URL = 'https://api.stackexchange.com/2.1/search'

_QUERY_PFX = 'query:'
_SINK_PFX = 'sink:'

_DEFAULT_SEARCH_PARAMS = {
    'site': 'stackoverflow'
}

SINKS = {}

class SOUser(object):
    def __init__(self, dict):
        self.nick = dict['display_name']
        self.link = dict['link']
        self.img = dict['profile_image']


class SOQuestion(object):
    def __init__(self, dict):
        self.link = dict['link']
        self.title = dict['title']
        self.owner = SOUser(dict['owner'])
        self.asked_at = datetime.datetime.fromtimestamp(dict['creation_date'])
        self.tags = dict['tags']
        for prop in dir(self.owner):
            setattr(self, 'owner_' + prop, getattr(self.owner, prop))


class SOQuery(object):
    def __init__(self, id, conf):
        self.id = id
        self.last_fetch = conf.get('last_fetch')
        self.query = conf.get('query', 'wrong question')
        self.site = conf.get('site', 'stackoverflow')
        self.tags = conf.get('tags')
        self.label = conf.get('label')

    def resolve(self, from_time):
        params = {
            'site': self.site,
            'intitle': self.query
        }
        if self.tags:
            params['tags'] = self.tags
        if self.last_fetch:
            params['fromdate'] = self.last_fetch

        if from_time:
            params['fromdate'] = from_time
        resp = requests.get(_SEARCH_URL, params=params)
        return [SOQuestion(x) for x in resp.json()['items']]


class HipChatNotifSink(object):
    def __init__(self, conf, tenv):
        self.hc = hipchat.HipChat(token=conf['token'])
        self.room = conf['room']
        self.sender = conf['from']
        self.tmpl = tenv.get_template('hipchat_msg.html')
        self.color = conf.get('color', 'green')
        self.mentions = conf.get('mentions')
        if self.mentions:
            self.mentions = '@' + re.sub(r"[,| ;]", " @", self.mentions)

    def notify(self, query, questions):
        for question in questions:
            msg = self.tmpl.render(query=query, question=question)
            self.hc.message_room(self.room, self.sender, msg, 'html',
                self.color)
        if self.mentions and questions:
            self.hc.message_room(self.room, self.sender, self.mentions,
                color=self.color)


def main(argv=sys.argv):
    config = _parse_config(argv)
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    template_env = Environment(loader=PackageLoader('soqun', 'templates'))
    _do_poll(config, template_env)


def _do_poll(config, tenv):
    queries = []
    sinks = []

    times = _get_times(config)
    for conf_sec, conf in config.iteritems():
        if conf_sec.startswith(_QUERY_PFX):
            queries.append(SOQuery(conf_sec, conf))
        elif conf_sec.startswith(_SINK_PFX):
            sinks.append(SINKS[conf['type']](conf, tenv))

    for query in queries:
        questions = query.resolve(times.get(query.id))
        for sink in sinks:
            sink.notify(query, questions)

        times[query.id] = int(time.mktime(datetime.datetime.now().timetuple()))

    _save_times(config, times)

def _get_times(conf):
    file = conf['soqun'].get('timestamp_storage')
    if not file:
        return {}
    if not os.path.isfile(file):
        return {}
    with open(file, 'r') as inp:
        content = inp.read()
        return json.loads(content)


def _save_times(conf, times):
    file = conf['soqun'].get('timestamp_storage')
    if not file:
        return
    with open(file, 'w') as inp:
        inp.write(json.dumps(times))


def _parse_config(argv):
    if len(argv) < 2:
        print "Usage soqun_poll configfile.ini"
        exit(1)

    path = argv[1]
    if not os.path.isfile(path):
        print "Given configuration file does not exist"
        exit(1)
    parser = ConfigParser.ConfigParser({'__file__': path,
                                        'here': os.path.dirname(path)})
    parser.read([path])

    config = {}
    for section in parser.sections():
        config[section] = _tuples_to_dict(parser.items(section))
    return config


def _tuples_to_dict(tuples):
    result = {}
    for k, v in tuples:
        result[k] = v
    return result


SINKS['hipchat'] = HipChatNotifSink

if __name__ == '__main__':
    main()
