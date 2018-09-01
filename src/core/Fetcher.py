import os
import re
import shutil as files
from os import path
from os.path import isfile, join

from src import config
from src.domain.Key import Key
from src.domain.Mod import Mod

INPUT_XML_PATTERN = 'id="PCInput".+<!--\s*\[BASE_CharacterMovement\]\s*-->'
xmlpattern = re.compile("<Var.+\/>", re.UNICODE)
inputpattern = re.compile(r"(\[.*\]\s*(IK_.+=\(Action=.+\)\s*)+\s*)+", re.UNICODE)
userpattern = re.compile(r"(\[.*\]\s*(.*=(?!.*(\(|\))).*\s*)+)+", re.UNICODE)


class Fetcher:

    def fetch(self, modPath):
        if self.isArchive(modPath):
            modPath = self.extract(modPath)

        if self.isValidModFolder(modPath):
            return self.fetchModFromDirectory(modPath)
        else:
            return Mod()

    # tested
    def isValidModFolder(self, modPath):
        for currentDir, _, _ in os.walk(modPath):
            if self.isDataFolder(path.split(currentDir)[1]) and self.containContentFolder(currentDir):
                return True
        return False

    def fetchModFromDirectory(self, modPath):
        mod = Mod(path.split(modPath)[1])
        for currentDir, _, _ in os.walk(modPath):
            self.fetchDataIfRelevantFolder(currentDir, mod)
            self.fetchDataFromRelevantFiles(currentDir, mod)
        return mod

    # tested
    def isDataFolder(self, dir):
        return bool(re.match("^mod.*", dir, re.IGNORECASE))

    # tested
    def containContentFolder(self, dir):
        return "content" in (dr.lower() for dr in self.getAllFolersFromDirectory(dir))

    # tested
    def getAllFolersFromDirectory(self, dir):
        return [f for f in os.listdir(dir) if os.path.isdir(join(dir, f))]

    # tested
    def getAllFilesFromDirectory(self, dir):
        return [f for f in os.listdir(dir) if isfile(join(dir, f))]

    # tested
    def fetchDataIfRelevantFolder(self, currentDir, mod):
        dirName = path.split(currentDir)[1]
        if self.containContentFolder(currentDir):
            if self.isDataFolder(dirName):
                mod.files.append(dirName)
            else:
                mod.dlcs.append(dirName)

    def fetchDataFromRelevantFiles(self, currentDir, mod):
        files = self.getAllFilesFromDirectory(currentDir)
        for file in files:
            if self.isMenuXmlFile(file):
                mod.menus.append(file)
            elif self.isTxtOrInputXmlFile(file):
                with open(currentDir + "/" + file, 'r') as myfile:
                    text = myfile.read()
                    if file == "input.xml":
                        text = self.fetchRelevantDataFromInputXml(text, mod)
                    self.fetchAllXmlKeys(file, text, mod)
                    mod.inputsettings.append(self.fetchInputSettings(text))
                    mod.usersettings.append(self.fetchUserSettings(text))

    # tested
    def isMenuXmlFile(self, file):
        return re.match(".+\.xml$", file) and not re.match("^input\.xml$", file)

    # tested
    def isTxtOrInputXmlFile(self, file):
        return re.match("(.+\.txt)|(input\.xml)$", file)

    def fetchRelevantDataFromInputXml(self, filetext, mod):
        self.getHiddenKeysIfExistFromInputXml(filetext, mod)
        searchResult = re.search(INPUT_XML_PATTERN, filetext, re.DOTALL)
        return self.removeXmlComments(searchResult.group(0))

    def getHiddenKeysIfExistFromInputXml(self, filetext, mod):
        temp = re.search('id="Hidden".+id="PCInput"', filetext, re.DOTALL)
        if (temp):
            hiddentext = temp.group(0)
            hiddentext = self.removeXmlComments(hiddentext)
            xmlkeys = xmlpattern.findall(hiddentext)
            for key in xmlkeys:
                key = self.removeMultiWhiteSpace(key)
                mod.hidden += key

    # tested
    def removeXmlComments(self, filetext):
        filetext = re.sub('<!--.*?-->', '', filetext)
        filetext = re.sub('<!--.*?-->', '', filetext, 0, re.DOTALL)
        return filetext

    def fetchAllXmlKeys(self, file, filetext, mod):
        xmlKeys = self.fetchXmlKeys(filetext)
        if "hidden" in file and xmlKeys:
            mod.hiddenkeys += xmlKeys
        else:
            mod.xmlkeys += xmlKeys

    def fetchInputSettings(self, filetext):
        found = []
        inputsettings = inputpattern.search(filetext)
        if (inputsettings):
            res = re.sub("\n+", "\n", inputsettings.group(0))
            arr = str(res).split('\n')
            if '' in arr:
                arr.remove('')
            context = ''
            for key in arr:
                if key[0] == "[":
                    context = key
                else:
                    newkey = Key(context, key)
                    found += newkey
        return found

    # tested
    def fetchUserSettings(self, filetext):
        usersettings = userpattern.search(filetext)
        if (usersettings):
            res = re.sub("\n+", "\n", usersettings.group(0))
            return str(res)

    def fetchXmlKeys(self, filetext):
        found = []
        xmlkeys = xmlpattern.findall(filetext)
        for key in xmlkeys:
            key = self.removeMultiWhiteSpace(key)
            found += key
        return found

    # tested
    def removeMultiWhiteSpace(self, key):
        key = re.sub("\s+", " ", key)
        return key

    # tested
    def isArchive(self, modPath):
        return re.match(".+\.(zip|rar|7z)$", path.basename(modPath))

    def extract(self, modPath):
        extractedDir = config.data.extracted
        if (path.exists(extractedDir)):
            files.rmtree(extractedDir)
        os.mkdir(extractedDir)
        os.subprocess.call('7-Zip\\7z x "' + modPath + '" -o' + '"' + extractedDir + '"')
        return extractedDir
