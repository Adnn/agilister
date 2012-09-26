import urllib2
from lxml import etree
import os
from xml.dom.minidom import parse
import DataElement

## \brief Abstract class to represent the different choices to fill a data element (in the data DOM) based on the type of web element it will be linked to in a given website.
# For example if a data element is linked to a select web element, the only choices for it's values would be the nested option's values.
class Choices(object):
    pass

## \brief Specialization of Choices for select web elements. 
class WebElementChoices(Choices):
    def __init__(self, promptText, valueList):
        self._promptText = promptText
        self._valueList = valueList

    ## \return The value of the valueId(th) option (0 indexed)
    def getValue(self, valueId):
        return self._valueList[valueId]
    
    def getIndex(self, value):
        return self._valueList.index(value)

    ## \brief This method handles communication with the user so he can select a value for the data element.
    
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
        
## \brief Specialization of Choices for free text web elements. 
class TextChoices(Choices):
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
        


## \brief A wrapper around Website metadata that is found in $sitename.xml file.
# It gives access to the different fields found in the metadata, through getters that are the centralized place knowing about the DOM structure.
class WebsiteDetails(object): 
    ## Ctor
    # \param websiteName The website name for which the metadata should be loaded. The code will look in the default websites directory ($AGILISTER/websites) for the file <i>websiteName</i>.xml
    def __init__(self, websiteName):
        websiteFile = os.path.join(os.environ[DataElement.AGILISTER_ENVAR], DataElement.WEB_FOLDER, websiteName+".xml")
        if(os.path.exists(websiteFile)) :
            self._dom = parse(websiteFile)
        else:
            raise Exception("Cannot find the website " + website + ".")
        self._name = websiteName
        self._generateDataTagDictionnary()

    ## \brief Initializes a dictionnary that will map each data tagname (the tagnames in the data DOM) present in the website file, to the mapElement (relationElement) listing it. It then looks like {dataTagname : {"map":mapElement}}.
    # The dictionary value element is a nested dictionary, so it is possible to attach additional information to each data tagname.  
    def _generateDataTagDictionnary(self):
        self._dataTagToMap= {}
        for mapping in self.getMappings():
            self._dataTagToMap[mapping.firstChild.nodeValue] = {"map" : mapping}

    ## \return The website name
    def getName(self):
        return self._name

    ## \return The website post url (i.e. the first page of the posting form)
    def getPostUrl(self):
        return self._dom.firstChild.getElementsByTagName("url").item(0).getElementsByTagName("post").item(0).firstChild.nodeValue

    ## \return An xml element describing a successfull post consequence. It could in particular contain a XPath attribute defining a web element that becomes visible when posting completes successfully.
    def getSuccessElement(self):
        return self._dom.firstChild.getElementsByTagName("success").item(0)

    ## \return A string containing Python code that should be executed when the post url is loaded, <b>before</b> any attempt to fill web elements.
    def getPrecode(self):
        precodeElem = self._dom.firstChild.getElementsByTagName("precode").item(0)
        if precodeElem:
            return precodeElem.firstChild.nodeValue
        return None

    ## \return the complete <map> xml element, containing the nested <mapping> elements.
    def getMappings(self):
        return self._dom.firstChild.getElementsByTagName("fieldmap").item(0).getElementsByTagName("map")

    ## \return A single <mapping> xml element, which is a kind of relationElement referred as mapElement in the documentation.
    # The returned element is mapping a web element (defined by its XPath) to a data DOM tagname (meaning this tag contains the data to fill the pointed web element).
    def getMapping(self, dataFieldTagName):
        if dataFieldTagName in self._dataTagToMap:
            return self._dataTagToMap[dataFieldTagName]["map"]
        else:
            return None

    ## \return The <photo> xml element, which is a relationElement referred as photoElement in the documentation.
    # The returned photoElement describes how to post images when posting on the website.
    def getPhotoElement(self):
        return self._dom.firstChild.getElementsByTagName("photo").item(0)

    def getWebsiteDatafile(self):
        dataFile = os.path.join(os.environ[DataElement.AGILISTER_ENVAR], DataElement.WEB_FOLDER, self._name+"-data.xml")
        if os.path.exists(dataFile):
            return dataFile
        else:
            return None

    ## \return the Choices instance corresponding to the given data tagname.
    # If the Choices instance was not already generated, it is and then attached to the corresponding dataTag value, as a dictionnary entry with the key "choices". Dictionary looks like {tagname : {"map" : mapElement, "choices" : choicesInstance[, ...]}}
    def getDataTagChoices(self, tagName):
        if tagName in self._dataTagToMap:
            if "choices" in self._dataTagToMap[tagName]:
                return self._dataTagToMap[tagName]["choices"]
            else:
                return self._generateChoices(tagName)
        else:
            return None

    ## Factory method for Choices, instanciating the correct specialization corresponding to the web element linked to the given tagname.
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
