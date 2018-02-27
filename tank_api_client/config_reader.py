# -*- coding: utf-8 -*-

import os
import re
import ConfigParser


class RootIsNotCorrect(Exception):
    pass


class ConfigReader(object):
    LT_PATH = '/'
    GIT_USED = False
    COMMON_INI = ['common.ini']
    MAX_DEEP_READ = 10
    YANDEX_TANK_INI = '~/.yandex-tank'
    SALTS_SEC = 'salts'
    def __init__(self, file_path):
        self.config_path = file_path
        self.content = {}
        self.default = {}
        self.read_configs = []
        commons = self.find_common_ini()
        for c in commons:
            (root, common) = c
            file_path = os.path.join(root, common)
            self.read_ini(file_path)
        self.read_ini(os.path.expanduser(self.YANDEX_TANK_INI))
        self.read_ini(self.config_path)

    def find_common_ini(self):
        commons = []
        cdir = self.config_path
        nested = 0
        while nested < ConfigReader.MAX_DEEP_READ:
            cdir = os.path.dirname(cdir)
            files = [f for f in os.listdir(cdir)
                     if os.path.isfile(os.path.join(cdir, f))]
            commons += list(reversed([(cdir, c) for c in self.COMMON_INI if c in files]))
            if ConfigReader.LT_PATH == cdir:
                break
            nested += 1
        return reversed(commons)

    def read_ini(self, file_path):
        config = ConfigParser.RawConfigParser()
        config.read(file_path)

        def_values = config.defaults()
        for k in def_values:
            self.default.update({k: def_values[k]})

        sections = config.sections()
        for sec in sections:
            if sec not in self.content:
                self.content[sec] = {}
            for (k,v) in config.items(sec):
                self.content[sec].update({k: v})

        for sec in self.content:
            for k in self.default:
                self.content[sec].update({k: self.default[k]})

        self.read_configs.append(file_path)

    def get_content(self):
        return self.content

    def get_read_configs(self):
        return self.read_configs

    def save_ini(self, file_path = None):
        if not file_path:
            file_name, file_ext = os.path.splitext(self.config_path)
            file_path = "%s.tmp" % file_name
        config = ConfigParser.RawConfigParser()
        for sec in self.content:
            config.add_section(sec)
            for key in self.content[sec]:
                config.set(sec, key, self.content[sec][key])
        if ConfigReader.GIT_USED \
                and (not config.has_option(ConfigReader.SALTS_SEC,
                                           'scenario_id')):
            if ConfigReader.SALTS_SEC not in config.sections():
                config.add_section(ConfigReader.SALTS_SEC)
            config.set(ConfigReader.SALTS_SEC, 'scenario_path',
                    re.sub('^%s/' % ConfigReader.LT_PATH, '',
                            self.config_path))
        with open(file_path, 'w') as f:
            config.write(f)
        return file_path
