from xml.dom.minidom import parse, parseString
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
import Arguments
import DataElement
import WebsiteDetails
import time
import sys, os, re

# for save of select :
#select.first_selected_option.get_attribute("value")


xmlMerge = u'<?xml version="1.0" encoding="utf-8"?><merge></merge>'

# The merging order will define the precedence of the files (in case of duplicate element)
def mergeData(xmlOrderedList) :
    domMerge = parseString(xmlMerge)
    for xmlFile in xmlOrderedList:
        domMerge.firstChild.appendChild(parse(xmlFile).firstChild)
    return domMerge

def postAdOnWebsite(adDirectory, userFile, website):
    adFile = os.path.join(adDirectory, DataElement.ADVERTISEMENT_FILE)
    if not os.path.exists(adFile):
        sys.stderr.write("Cannot find the advertisement file " + adFile + ".")
        sys.exit(-2)
    adSubdir = os.path.basename(os.path.normpath(adDirectory))
    print os.linesep + "### " + adSubdir + "(" + website.getName() + ") ###"
    advertisementDom = mergeData((adFile, website.getWebsiteDatafile(), userFile))

    browser = webdriver.Chrome()
    browser.get(website.getPostUrl())

# \todo : enhance security
    precode = website.getPrecode()
    if precode:
        exec precode

    photoElement = website.getPhotoElement()
    if photoElement :
        images = [f for f in os.listdir(adDirectory) if re.match(r'[0-9]+\.(JPG|jpg)', f)]
# \todo : also implement a per website image limit
        for imageFile in images :
            DataElement.PhotoFiller(website.getName(), photoElement, os.path.join(adDirectory, imageFile)).fill(browser)
            time.sleep(DataElement.FILL_FREEZETIME)

    dataElement = None
    for mapping in website.getMappings():
         dataElement = DataElement.build(website.getName(),  mapping, advertisementDom) 

         if dataElement.getValue() :
             if not dataElement.fill(browser):
                 sys.stderr.write("\tError occured while attempting to write " + dataElement.getTagName() + " to website " + website.getName() + os.linesep)
             time.sleep(DataElement.FILL_FREEZETIME)

    if DataElement.WebFiller(website.getName(), website.getSuccessElement()).checkVisibility(browser):
        print "Successfully posted advertisement for " + adSubdir + "."
        try:
            browser.quit()
        except OSError as e:
            #print "(Catched OSError : " + str(e) + ".)"
            a = []
    else:
        print "It seems that errors occurent posting advertisement for " + adSubdir + ". Browser was not closed."


parser = Arguments.Arguments("The advertisement poster.").parser
parser.add_argument("-u", "--user", type=unicode, required=True, help="The user on which behalf the advertisements will be posted.")
args = parser.parse_args()

userFile = os.path.join(os.environ[DataElement.AGILISTER_ENVAR], DataElement.USER_FOLDER, args.user+".xml")
if not os.path.exists(userFile):
    sys.stderr.write("Cannot find the user file for " + args.user + ".")
    sys.exit(-1)
adDirectory = args.directory

for website in [WebsiteDetails.WebsiteDetails(websiteName) for websiteName in args.websites]:
    postAdOnWebsite(adDirectory, userFile, website)
