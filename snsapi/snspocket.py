# -*- coding: utf-8 -*-

'''
snspocket: the container class for snsapi's

'''

# === system imports ===
try:
    import json
except ImportError:
    import simplejson as json
from os.path import abspath

# === snsapi modules ===
import snstype
import utils
from utils import JsonObject
from utils import console_output
from snslog import SNSLog
logger = SNSLog
import plugin

# === 3rd party modules ===

class SNSPocket(dict):
    """The container class for snsapi's"""
    def __init__(self):
        super(SNSPocket, self).__init__()
        self.jsonconf = {}

    def __iter__(self):
        """
        By default, the iterator only return opened channels.
        """
        l = []
        for c in self.itervalues():
            if c.jsonconf['open'] == 'yes':
                l.append(c.jsonconf['channel_name'])
        return iter(l)

    def read_config(self, \
            fn_channel = 'conf/channel.json',\
            fn_pocket = 'conf/pocket.json'):
        """
        Read configs:
        * channel.conf
        * pocket.conf
        """
        try:
            with open(abspath(fn_channel), "r") as fp:
                allinfo = json.load(fp)
                for site in allinfo:
                    logger.debug(json.dumps(site))
                    #if site['open'] == "yes" :
                    p = getattr(plugin, site['platform'])
                    c = getattr(p, p._entry_class_)
                    if c:
                        self[site['channel_name']] = c(site)
                        #TODO:
                        #    This is a work around to store rich 
                        #    channel information in the snsapi 
                        #    class. The snsapi class should be 
                        #    upgrade so that jsonconf is its 
                        #    default entrance to access all 
                        #    config matters. The current hard 
                        #    code attributes are not friendly to
                        #    upgrades. Say you have to write one
                        #    more assignment if there is one more 
                        #    config entry. e.g.
                        #    self.open = channel['open']
                        self[site['channel_name']].jsonconf = site
                    else:
                        raise errors.NoSuchPlatform
        except IOError:
            raise errors.NoConfigFile

        try:
            with open(abspath(fn_pocket), "r") as fp:
                allinfo = json.load(fp)
                self.jsonconf = allinfo
        except IOError:
            raise errors.NoConfigFile

    def save_config(self, \
            fn_channel = 'conf/channel.json',\
            fn_pocket = 'conf/pocket.json'):
        """
        Save configs: reverse of read_config

        Configs can be modified during execution. snsapi components 
        communicate with upper layer using Python objects. Pocket 
        will be the unified place to handle file transactions.  
        
        """

        conf_channel = []
        for c in self.itervalues():
            conf_channel.append(c.jsonconf)

        conf_pocket = self.jsonconf

        try:
            json.dump(conf_channel, open(fn_channel, "w"), indent = 2)
            json.dump(conf_pocket, open(fn_pocket, "w"), indent = 2)
        except:
            raise errors.SNSPocketSaveConfigError
        
    def list(self, verbose = False):
        console_output("\n")
        console_output("Current channels:")
        for cname in self.iterkeys():
            c = self[cname].jsonconf
            console_output("   * %s: %s %s" % \
                    (c['channel_name'],c['platform'],c['open']))
            if verbose:
                console_output("    %s" % json.dumps(c))
        console_output("\n")

    def auth(self, channel = None):
        """docstring for auth"""
        if channel:
            self[c].auth()
        else:
            for c in self.itervalues():
                c.auth()

    def home_timeline(self, count = 20, channel = None):
        """
        Route to home_timeline method of snsapi. 
        
        :param channel:
            The channel name. Use None to read all channels
        """
        status_list = snstype.StatusList()
        if channel:
            status_list.extend(self[channel].home_timeline(count))
        else:
            for c in self.itervalues():
                if c.jsonconf['open'] == "yes":
                    status_list.extend(c.home_timeline(count))
        return status_list

    def update(self, text, channel = None):
        """
        Route to update method of snsapi. 
        
        :param channel:
            The channel name. Use None to update all channels
        """
        if channel:
            return self[channel].update(text)
        else:
            re = {}
            for c in self.itervalues():
                if c.jsonconf['open'] == "yes":
                    re[c.jsonconf['channel_name']] = c.update(text)
            return re

    def reply(self, statusID, text, channel = None):
        """
        Route to reply method of snsapi. 
        
        :param channel:
            The channel name. Use None to automatically select
            one compatible channel. 
        """
        if channel:
            return self[channel].reply(statusID, text)
        else:
            for c in self.itervalues():
                if c.jsonconf['open'] == "yes":
                    if c.jsonconf['platform'] == statusID.platform:
                        return c.reply(statusID, text)
