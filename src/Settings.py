import sublime

import os
from .File import File

PACKAGE_PATH    = sublime.packages_path()
#SETTINGS_PATH   = PACKAGE_PATH + '\\' + __package__ + '\\settings\\JF.sublime-settings'
SETTINGS_PATH   = PACKAGE_PATH + '\\JF\\settings\\JF.sublime-settings'

# Capturar definições em arquivo de configurações
class Settings:
    def all(self):
        if os.path.exists(SETTINGS_PATH):
            self.items = File.loadJson(SETTINGS_PATH)
        else:
            self.items = {}

        return self.items

    def get(self, key_path='', default=None):
        items   = self.all()

        if len(key_path) <= 0:
            return

        res     = items
        keys    = key_path.split('.')

        for key in keys:
            res = res.get(key)
            
            if res is None:
                return default
        
        return res
