import os

from library.SettingsEntry import SettingsEntry


class AppData:
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if AppData.__instance is None:
            AppData()
        return AppData.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if AppData.__instance is not None:
            raise Exception("This class [AppData] is a singleton!")
        else:
            AppData.__instance = self

    @staticmethod
    def getSettingsEntry():
        settings_entry = SettingsEntry.getInstance()
        return settings_entry
