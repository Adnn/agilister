import urllib2
from lxml import etree
import os
from xml.dom.minidom import parse
import DataElement

class WebElementChoices(object):
    def __init__(self, promptText, valueList):
        self._promptText = promptText
        self._valueList = valueList

    def getValue(self, valueId):
        return self._valueList[valueId]
    
    def getIndex(self, value):
        return self._valueList.index(value)

    def promptUser(self, banner, currentValue):
        print self._promptText
        if not currentValue:
            currentValue=""
        else:
            currentValue=str(self.getIndex(currentValue))
        try:
            print banner
            optionId = int(raw_input("Enter new value[" + currentValue + "] : "))
            newValue = self.getValue(optionId)
        except ValueError, IndexError:
            newValue = None

        return newValue
        
class TextChoices(object):
    def __init__(self, promptText):
        self._promptText = promptText

    def promptUser(self, banner, currentValue):
        print self._promptText
        if not currentValue:
            currentValue=""
            
        print banner
        newValue = raw_input("Enter new value[" + currentValue + "] : ")

        if len(newValue)==0:
            newValue = None

        return newValue
        


class WebsiteDetails(object): 
    def __init__(self, websiteName):
        websiteFile = os.path.join(os.environ[DataElement.AGILISTER_ENVAR], DataElement.WEB_FOLDER, websiteName+".xml")
        if(os.path.exists(websiteFile)) :
            self._dom = parse(websiteFile)
        else:
            raise Exception("Cannot find the website " + website + ".")
        self._name = websiteName
        self._generateDataTagDictionnary()

    def _generateDataTagDictionnary(self):
        self._dataTagToMap= {}
        for mapping in self.getMappings():
            self._dataTagToMap[mapping.firstChild.nodeValue] = {"map" : mapping}

    def getName(self):
        return self._name

    def getPostUrl(self):
        return self._dom.firstChild.getElementsByTagName("url").item(0).getElementsByTagName("post").item(0).firstChild.nodeValue

    def getSuccessElement(self):
        return self._dom.firstChild.getElementsByTagName("success").item(0)

    def getPrecode(self):
        return self._dom.firstChild.getElementsByTagName("precode").item(0).firstChild.nodeValue

    def getMappings(self):
        return self._dom.firstChild.getElementsByTagName("fieldmap").item(0).getElementsByTagName("map")

    def getMapping(self, dataFieldTagName):
        if dataFieldTagName in self._dataTagToMap:
            return self._dataTagToMap[dataFieldTagName]["map"]
        else:
            return None

    def getPhotoElement(self):
        return self._dom.firstChild.getElementsByTagName("photo").item(0)

    def getWebsiteDatafile(self):
        dataFile = os.path.join(os.environ[DataElement.AGILISTER_ENVAR], DataElement.WEB_FOLDER, self._name+"-data.xml")
        if os.path.exists(dataFile):
            return dataFile
        else:
            return None

    def getDataTagChoices(self, tagName):
        if tagName in self._dataTagToMap:
            if "choices" in self._dataTagToMap[tagName]:
                return self._dataTagToMap[tagName]["choices"]
            else:
                return self._generateChoices(tagName)
        else:
            return None

    def _generateChoices(self, tagName):
        mapping = self.getMapping(tagName)
        output = u""
        optionList = []

        postPage = urllib2.urlopen(self.getPostUrl())
        htmlparser = etree.HTMLParser()
        webpageTree = etree.parse(postPage, htmlparser)

        if mapping.getAttribute(DataElement.TYPE_ATTR)==DataElement.TYPE_SELECT:
            select = webpageTree.xpath(mapping.getAttribute(DataElement.XPATH))[0]
            selectorId = 0
            for option in select :
                if option.get("disabled") :
                    output += option.text + os.linesep
                elif option.get("value") :
                    output += "\t" + str(selectorId) + " : " + option.text + os.linesep
                    optionList.append(option.get("value"))
                    selectorId+=1

            choices = WebElementChoices(output, optionList)
        elif mapping.getAttribute(DataElement.TYPE_ATTR)==DataElement.TYPE_RADIO:
            # \todo : Implement radio choices
            raise Exception("Choices for radio not implemented yet.")
        else:
            choices = TextChoices(output)

        self._dataTagToMap[tagName]["choices"] = choices
        return choices
