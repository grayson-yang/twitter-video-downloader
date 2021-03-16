import json
import os
from pathlib import Path


class SettingsEntry:
    __instance = None
    __config_settings_path = ""
    __settings_json = json.loads("{}")

    @staticmethod
    def getInstance():
        """ Static access method. """
        if SettingsEntry.__instance is None:
            SettingsEntry()
        return SettingsEntry.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if SettingsEntry.__instance is not None:
            raise Exception("This class [SettingsEntry] is a singleton!")
        else:
            SettingsEntry.__instance = self

    def setSettingsPath(self, path):
        self.__config_settings_path = path

    def getSettingsPath(self):
        return self.__config_settings_path

    def loadSettings(self):
        lines = []
        file = self.__config_settings_path
        if Path.exists(Path(file)) is False:
            Path(file).touch()
        with open(Path(file), 'r') as f1:
            f1.seek(0, 0)
            lines = f1.readlines()
        for i in range(0, len(lines)):
            lines[i] = lines[i].rstrip('\n')
        content = ''.join(lines)
        self.__settings_json = json.loads(content)
        return self.__settings_json

    def saveSettings(self):
        content = json.dumps(self.__settings_json)
        file = self.__config_settings_path
        with open(file, 'w') as f:
            f.writelines(content)

    def getDuration(self):
        return self.__settings_json["network"]["duration"]

    def setDuration(self, duration):
        self.__settings_json["network"]["duration"] = duration

    def getResolution(self):
        return self.__settings_json["media"]["resolution"]

    def setResolution(self, resolution):
        self.__settings_json["media"]["resolution"] = resolution

    def getMp4(self):
        return self.__settings_json["media"]["mp4"]

    def setMp4(self, mp4):
        self.__settings_json["media"]["mp4"] = mp4

    def getRootStorage(self):
        return self.__settings_json["storage"]["root"]

    def setRootStorage(self, folder):
        self.__settings_json["storage"]["root"] = folder


if __name__ == '__main__':
    # Instance Initiation
    settingsEntry = SettingsEntry.getInstance()
    settingPath = os.path.abspath('../config/settings.json')
    settingsEntry.setSettingsPath(settingPath)
    settingPath = settingsEntry.getSettingsPath()
    print("Settings Path: " + settingPath)
    # Scenario 1, load settings configuration
    settingsJson = settingsEntry.loadSettings()
    print("Settings: " + json.dumps(settingsJson))
    # Scenario 2, update settings configuration
    settingsEntry.setRootStorage("/home/Downloads")
    settingsEntry.saveSettings()
    settingsJson = settingsEntry.loadSettings()
    print("Settings: " + json.dumps(settingsJson))
