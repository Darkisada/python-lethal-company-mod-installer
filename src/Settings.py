from __future__ import annotations
from src.Utils import getCurrentDir, success
from src.ModSetting import ModSetting
from src.Version import Version
from src.SessionConstants import SessionConstants
import requests, yaml, os, json, sys

class Settings:
    configZipUrl: str
    downloadUserAgent: str
    modDownloadUrl: str
    modPageUrl: str

    modSettings: list[ModSetting] = []

    _originalSettings: dict

    def __init__(self, dict: dict):
        settings: dict         = dict["settings"]
        self._originalSettings = dict["settings"]
        self.configZipUrl      = str(settings["configZipUrl"])
        self.downloadUserAgent = str(settings["downloadUserAgent"])
        self.modDownloadUrl    = str(settings["modDownloadUrl"])
        self.modPageUrl        = str(settings["modPageUrl"])

        SessionConstants.PAGE_DOWNLOAD_URL = self.modPageUrl
        SessionConstants.MOD_DOWNLOAD_URL = self.modDownloadUrl
        SessionConstants.USER_AGENT       = self.downloadUserAgent

        if "mods" not in settings:
            return

        for modSetting in settings["mods"]:
            self.modSettings.append(ModSetting(
                modSetting,
                Version(settings["mods"][modSetting]["version"]),
                settings["mods"][modSetting]["pathmap"],
                settings["mods"][modSetting]["forcePin"] if "forcePin" in settings["mods"][modSetting] else None
            ))

    def getModSetting(self: Settings, modName: str) -> ModSetting | None:
        for modSetting in self.modSettings:
            if modSetting.fullModName == modName:
                return modSetting

            if modSetting.modName == modName:
                return modSetting

        return None

    def setModSetting(self: Settings, modSetting: ModSetting) -> None:
        for i in range(len(self.modSettings)):
            if self.modSettings[i].fullModName == modSetting.fullModName:
                self.modSettings[i] = modSetting
                return

        self.modSettings.append(modSetting)

    def toJSON(self: Settings) -> dict:
        return {
            "settings": {
                "configZipUrl": self.configZipUrl,
                "downloadUserAgent": self.downloadUserAgent,
                "modDownloadUrl": self.modDownloadUrl,
                "modPageUrl": self.modPageUrl,
                "mods": {
                    modSetting.fullModName: modSetting.toJSONForSettings() for modSetting in self.modSettings
                }
            }
        }

    @staticmethod
    def autoload() -> Settings:
        Current_Path = getCurrentDir()

        files = [
            Current_Path + "/settings.yaml",
            Current_Path + "/settings.test.yaml",
            Current_Path + "/../settings.yaml",
            Current_Path + "/../settings.test.yaml"
        ]

        settingsFile = None
        for file in files:
            if os.path.exists(file) and os.path.isfile(file):
                settingsFile = file
                break

        return Settings.loadFromFile(settingsFile)

    @staticmethod
    def loadFromFile(path: str | None = None) -> Settings:
        contents = ''

        if path == None:
            print("Downloading settings.yaml...")
            r = requests.get(SessionConstants.REMOTE_SETTINGS, allow_redirects=True)

            if r.status_code != 200:
                raise Exception("Error downloading settings.yaml")

            contents = r.content
        else:
            print("Loading " + os.path.basename(path) + "...")
            if not os.path.exists(path):
                raise Exception("Error loading settings.yaml")

            contents = open(path, "r")

        return Settings(yaml.load(contents, Loader=yaml.FullLoader))

    def printDiff(self: Settings) -> None:
        diffTo = self._originalSettings

        for modSetting in self.modSettings:
            isDiff = False
            if modSetting.fullModName not in diffTo["mods"]:
                isDiff = True
                print(f'New Mod {modSetting.fullModName} ({modSetting.modVersion})')
                continue

            oldMod = diffTo["mods"][modSetting.fullModName]

            if modSetting.modVersion.version != oldMod["version"]:
                isDiff = True
                print(f'New version for {modSetting.fullModName}: {oldMod["version"]} -> {modSetting.modVersion.version}')

            if modSetting.modPathMap != oldMod["pathmap"]:
                isDiff = True
                print(f'New pathmap for {modSetting.fullModName}')
                print("FROM: " + json.dumps(oldMod["pathmap"], indent=4))
                print("TO:   " + json.dumps(modSetting.modPathMap, indent=4))

            if "forcePin" in oldMod and modSetting.forcePin != oldMod["forcePin"]:
                isDiff = True
                print(f'New forcePin for {modSetting.fullModName}: {oldMod["forcePin"]} -> {modSetting.forcePin}')

            if isDiff:
                print()

    def saveToFile(self: Settings, path: str = "settings.yaml") -> None:
        with open(path, "w") as file:
            yaml.dump(self.toJSON(), file, sort_keys=False)

    def print(self: Settings) -> None:
        yaml.dump(self.toJSON(), sys.stdout, sort_keys=False)
