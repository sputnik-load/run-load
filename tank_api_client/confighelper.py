# -*- coding: utf-8 -*-

import json
import codecs
import ConfigParser
import StringIO
from os.path import expanduser
from urllib import quote, unquote


YANDEX_TANK_CONFIG_PATH = "%s/.yandex-tank" % expanduser('~')


def jsonstr2bin(jsonstr):
    return quote(jsonstr.encode('utf-8')).encode('base64', 'strict')


def bin2jsonstr(custom_data):
    return unquote(custom_data.decode('base64', 'strict'));


class UnicodeConfigParser(ConfigParser.RawConfigParser):
    def __init__(self, *args, **kwargs):
        ConfigParser.RawConfigParser.__init__(self, *args, **kwargs)

    def write(self, fp):
        """Fixed for Unicode output"""
        if self._defaults:
            fp.write("[%s]\n" % "DEFAULT")
            for (key, value) in self._defaults.items():
                fp.write("%s = %s\n" % (key, unicode(value).replace('\n', '\n\t')))
            fp.write("\n")

        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value) in self._sections[section].items():
                if key != "__name__":
                    fp.write("%s = %s\n" % (key, unicode(value).replace('\n','\n\t')))
            fp.write("\n")

    # This function is needed to override default lower-case conversion
    # of the parameter's names. They will be saved 'as is'.
    def optionxform(self, strOut):
        return strOut


class CustomConfig(object):

    def __init__(self, config_path):
        self.config = UnicodeConfigParser()
        self.config.readfp(codecs.open(config_path, 'r', 'utf-8'))

    def jsoncontent(self):
        content = {}
        for sec in self.config.sections():
            d = {}
            for opt in self.config.options(sec):
                d[opt] = self.config.get(sec, opt)
            content[sec] = d
        return json.dumps(content)

    def textcontent(self):
        final_config = StringIO.StringIO()
        self.config.write(final_config)
        return final_config.getvalue().encode('utf-8')

    def mergejson(self, line):
        custom = json.loads(line)
        for sec in custom:
            if not self.config.has_section(sec):
                self.config.add_section(sec)
            param = custom[sec]
            for k in param:
                self.config.set(sec, k, param[k])
