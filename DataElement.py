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
FILL_FREEZETIME = 2 

## \brief Helper method to determine if an attribute is "present" in a xml element
# It allows to emulate flags in xml elements. An attribute is said to be present if it's value is set to 1.
# \param xmlElement, element that will be searched against the attribute
# \param attributeName
def presentAttribute(xmlElement, attributeName) :
        return xmlElement.getAttribute(attributeName)==u"1"

## \brief Callback method for WebDriverWait.until() allowing to determine if a webpage element is currently displayed
# \param element Web element to be checked for visibility
# \return the element if it is displayed, None otherwise
def visible(element):
    if element.is_displayed():
        return element
    return None

## \brief Remove Dos and Unix endlines from a string, without replacing them.
def removeEndl(basestring) :
    return basestring.replace("\r\n","\n").replace("\n","")

## \brief Remove tabulations from a string, without replacing them.
def removeTab(basestring) :
    return basestring.replace("\t","")

## \brief An abstract class interfacing the ability to fill a Web element, independently from the datasource or the web element. The element that will be filled is described by a relationElement (xml) provided at construction.
# Subclasses can be implemented for different datasources or different web elements. They should then implement the _fillImpl() method.
class WebFiller(object):
    def __init__(self, website, relationElement):
        self.relationElement = relationElement

        self._website = website
        ## XPath to the Web element to be filled.
        self._webXpath = relationElement.getAttribute(XPATH)
        ## iframe containing the Web element.
        self._iframe = relationElement.getAttribute(IFRAME_ATTRIB)
        ## Should we submit() the Web element once filled
        self._submitFlag = presentAttribute(relationElement, SUBMIT_ATTR)

    ## \brief A wrapper to call any operation on a Web element if it is found.
    # \return True if the element was found, False otherwise.
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

    ## Public method that returns True if the pointed Web element is displayed on the Webpage, False if it is sill not visible after the defined timeout.
    def checkVisibility(self, webDriver):
        return self._webElementOperation(webDriver, None)

    def fill(self, webDriver):
        return self._webElementOperation(webDriver, self._fillOperation)

    def _fillOperation(self, inputElement):
        self._fillImpl(inputElement)
        if self._submitFlag:
            inputElement.submit()

    ## \todo : delete
    #def _submit(self, webDriver):
    #    return self._webElementOperation(webDriver, self._submitOperation)

    #def _submitOperation(self, inputElement):
    #    inputElement.submit()

## \brief A WebFiller specialised for image files.
# It was designed for Vivastreet simple "input-file" button and works with LeBonCoin thanks to the submit flag.
class PhotoFiller(WebFiller):
    ## Ctor
    # \param photoElement the xml relation element describing the Web photo element of website
    # \param photoPhile a string giving the absolute path to the image on the local filesystem
    def __init__(self, website, photoElement, photoFile):
        super(PhotoFiller, self).__init__(website, photoElement)
        self._value = photoFile

    def _fillImpl(self, inputElement):
        inputElement.send_keys(self._value)

## \brief A WebFiller specialization for elements whose value is found in a data DOM.
# Those data DOM list different values inside different tag pairs, whose tagname describe the content. Site agnostice content is found as a text element at first level inside the tag pairs. Site specific content is enclose in an extra tag pair whose tagname is the website name.
class DataElement(WebFiller):
    '''mapElement
    dataDom
    _website
    _fieldTag
    _fieldProper
    _webType
    _webXpath
    '''

    ## Ctor
    # \param mapElement is the xml relationElement. In addition to a relationElement, it contains a child text element giving the name of the tag containing the data (in dataDom).
    # \param dataDom the xml document listing the different fields value inside separate tag pairs.
    def __init__(self, website, mapElement, dataDom):
        super(DataElement, self).__init__(website, mapElement)
        self.dataDom = dataDom
        
        self._fieldTag = mapElement.firstChild.nodeValue
        self._fieldProper = presentAttribute(mapElement, PROPER)
        self._fieldElement = None

    ## Returns the tagname from dataDom associated to the pointed Web element
    def getTagName(self):
        return self._fieldTag

    ## Current value associated to the Web element (as found in the data DOM)
    def getValue(self):
        self._getFieldElement()
        if self._fieldElement:
            return self._fieldElement.firstChild.nodeValue
        else:
            return None

    ## Update/Create the value in the data DOM
    def setValue(self, newValue):
        self._getFieldElement(create=True)

        textValueNode = self._fieldElement.firstChild
        if textValueNode:
            textValueNode.nodeValue = newValue
        else:
            textValueNode = self.dataDom.createTextNode(newValue)
            self._fieldElement.appendChild(textValueNode)

    ## Type of the Web element
    def getType(self):
        return self._webType

    ## \brief Private method to get, and eventually create, the element from the data DOM that is pointed by mapElement.
    # It is responsible for implementing correct site agnostic / site specific data look-up.
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

## \brief Refinement of DataElement for select Web elements.
# For a select, the value found in the data DOM defines the select's option's value to be selected.
class SelectElement(DataElement):
    def __init__(self, website, mapElement, dataDom):
        super(SelectElement, self).__init__(website, mapElement, dataDom)
        self._webType = TYPE_SELECT

    def _fillImpl(self, inputElement):
        Select(inputElement).select_by_value(self.getValue())


## \brief Refinement of DataElement for free text Web elements.
# For a free text element, the value found in the data DOM is set as text input.
# The newlines are removed if the free text is not a textarea.
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

## \brief Refinement of DataElement for radio Web elements.
# For a radio element, the value found in the dataDOM is the XPath defining wich radio box should be checked. Thus the XPath found in the mapElement is not necessarily pointing to the exact element to check.
class RadioElement(DataElement):
    def __init__(self, website, mapElement, dataDom):
        super(RadioElement, self).__init__(website, mapElement, dataDom)
        self._webType = TYPE_RADIO
        self._webXpath = self.getValue()

    def _fillImpl(self, inputElement):
        inputElement.click()

## \brief Factory of DataElements, returning the correct final class instance depending on the type of Web element that the mapElement is pointing to.
def build(website, mapElement, dataDom):
    typ = mapElement.getAttribute("type")
    if typ==TYPE_SELECT:
        return SelectElement(website, mapElement, dataDom)
    if typ==TYPE_RADIO:
        return RadioElement(website, mapElement, dataDom)
    else:
        return TextElement(website, mapElement, dataDom)

## \brief Factory of DataElements, determining which map element to use based on the desired data DOM tagame.
def buildFromTag(website, dataFieldTagName, dataDom):
    mapElement = website.getMapping(dataFieldTagName)
    if mapElement:
        return build(website.getName(), mapElement, dataDom)
    else :
        return None
