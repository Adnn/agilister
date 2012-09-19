from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

ADVERTISEMENT_FILE = "annonce.xml"
AGILISTER_ENVAR = u"AGILISTER"
IFRAME_ATTRIB = u"iframe"
PROPER = u"proper"
TAG_ADVERTISEMENT = u"annonce"
TYPE_SELECT = u"select"
TYPE_TEXT = u"text"
TYPE_RADIO = u"radio"
WEB_FOLDER = u"websites"
USER_FOLDER = u"users"
TYPE_ATTR = u"type"
SUBMIT_ATTR = u"submit"
XPATH = u"xpath"

ELEMENT_TIMEOUT = 30
FILL_FREEZETIME = 0.5

def presentAttribute(xmlElement, attributeName) :
        return xmlElement.getAttribute(attributeName)==u"1"

def visible(element):
    if element.is_displayed():
        return element
    return None

def removeEndl(basestring) :
    return basestring.replace("\r\n","\n").replace("\n","")

def removeTab(basestring) :
    return basestring.replace("\t","")

class WebFiller(object):
    def __init__(self, website, relationElement):
        self.relationElement = relationElement

        self._website = website
        self._webXpath = relationElement.getAttribute(XPATH)
        self._iframe = relationElement.getAttribute(IFRAME_ATTRIB)

        self._submitFlag = presentAttribute(relationElement, SUBMIT_ATTR)

    def _webElementOperation(self, webDriver, operation):
        if self._iframe:
            webDriver.switch_to_frame(self._iframe)

        try:
            inputElement = WebDriverWait(webDriver, ELEMENT_TIMEOUT).until(lambda d: visible( webDriver.find_element(By.XPATH, self._webXpath) ))
            if operation:
                operation(inputElement)
        except TimeoutException:
            return False

        if self._iframe:
            webDriver.switch_to_default_content()
        return True

    def checkVisibility(self, webDriver):
        return self._webElementOperation(webDriver, None)

    def fill(self, webDriver):
        return self._webElementOperation(webDriver, self._fillOperation)

    def _fillOperation(self, inputElement):
        self._fillImpl(inputElement)
        if self._submitFlag:
            inputElement.submit()

    def submit(self, webDriver):
        return self._webElementOperation(webDriver, self._submitOperation)

    def _submitOperation(self, inputElement):
        inputElement.submit()

class PhotoFiller(WebFiller):
    def __init__(self, website, photoElement, photoFile):
        super(PhotoFiller, self).__init__(website, photoElement)
        self._value = photoFile

    def _fillImpl(self, inputElement):
        inputElement.send_keys(self._value)

class DataElement(WebFiller):
    '''mapElement
    dataDom
    _website
    _fieldTag
    _fieldProper
    _webType
    _webXpath
    '''

    def __init__(self, website, mapElement, dataDom):
        super(DataElement, self).__init__(website, mapElement)
        self.dataDom = dataDom
        
        self._fieldTag = mapElement.firstChild.nodeValue
        self._fieldProper = presentAttribute(mapElement, PROPER)
        self._fieldElement = None

    def getTagName(self):
        return self._fieldTag

    def getValue(self):
        self._getFieldElement()
        if self._fieldElement:
            return self._fieldElement.firstChild.nodeValue
        else:
            return None

    def setValue(self, newValue):
        self._getFieldElement(create=True)

        textValueNode = self._fieldElement.firstChild
        if textValueNode:
            textValueNode.nodeValue = newValue
        else:
            textValueNode = self.dataDom.createTextNode(newValue)
            self._fieldElement.appendChild(textValueNode)

    def getType(self):
        return self._webType

    def _getFieldElement(self, create=False):
        if not self._fieldElement:
            adElement = self.dataDom.getElementsByTagName(TAG_ADVERTISEMENT)[0]
            try:
                generalElement = self.dataDom.getElementsByTagName(self._fieldTag)[0]
            except IndexError:
                if not create :
                    return
                generalElement = self.dataDom.createElement(self._fieldTag)
                adElement.appendChild(generalElement)
            
            if not self._fieldProper:
                self._fieldElement = generalElement
                return

            try:
                properElement = generalElement.getElementsByTagName(self._website)[0]
            except IndexError:
                if not create :
                    return
                properElement = self.dataDom.createElement(self._website)
                generalElement.appendChild(properElement)

            self._fieldElement = properElement

class SelectElement(DataElement):
    def __init__(self, website, mapElement, dataDom):
        super(SelectElement, self).__init__(website, mapElement, dataDom)
        self._webType = TYPE_SELECT

    def _fillImpl(self, inputElement):
        Select(inputElement).select_by_value(self.getValue())

    def _generateChoices(self):
        output = u""
        optionList = []


class TextElement(DataElement):
    def __init__(self, website, mapElement, dataDom):
        super(TextElement, self).__init__(website, mapElement, dataDom)
        self._webType = TYPE_TEXT
        
    def _fillImpl(self, inputElement):
        value = self.getValue()
        if inputElement.tag_name!=u'textarea' :
            value = removeEndl(value) 
        value = removeTab(value)
        inputElement.send_keys(value)

class RadioElement(DataElement):
    def __init__(self, website, mapElement, dataDom):
        super(RadioElement, self).__init__(website, mapElement, dataDom)
        self._webType = TYPE_RADIO
        self._webXpath = self.getValue()

    def _fillImpl(self, inputElement):
        inputElement.click()

def build(website, mapElement, dataDom):
    typ = mapElement.getAttribute("type")
    if typ==TYPE_SELECT:
        return SelectElement(website, mapElement, dataDom)
    if typ==TYPE_RADIO:
        return RadioElement(website, mapElement, dataDom)
    else:
        return TextElement(website, mapElement, dataDom)

def buildFromTag(website, dataFieldTagName, dataDom):
    mapElement = website.getMapping(dataFieldTagName)
    if mapElement:
        return build(website.getName(), mapElement, dataDom)
    else :
        return None
