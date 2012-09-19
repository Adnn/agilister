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

parser = Arguments.Arguments("The advertisement poster.").parser
parser.add_argument("-u", "--user", type=unicode, required=True, help="The user on which behalf the advertisements will be poster.")
args = parser.parse_args()

userFile = os.path.join(os.environ[DataElement.AGILISTER_ENVAR], DataElement.USER_FOLDER, args.user+".xml")
if not os.path.exists(userFile):
    sys.stderr.write("Cannot find the user file for " + args.user + ".")
    sys.exit(-1)
website = WebsiteDetails.WebsiteDetails(args.websites[0])
advertisementDom = mergeData((os.path.join(args.directory, DataElement.ADVERTISEMENT_FILE), website.getWebsiteDatafile(), userFile))

print os.linesep + "### " + args.directory + " ###"
browser = webdriver.Chrome()
browser.get(website.getPostUrl())

# \todo : cleanup
exec website.getPrecode()

photoElement = website.getPhotoElement()
if photoElement :
    images = [f for f in os.listdir(args.directory) if re.match(r'[0-9]+\.(JPG|jpg)', f)]
# \todo : also implement a per website image limit
    for imageFile in images :
        DataElement.PhotoFiller(website.getName(), photoElement, os.path.join(args.directory, imageFile)).fill(browser)
        time.sleep(DataElement.FILL_FREEZETIME)

dataElement = None
for mapping in website.getMappings():
     dataElement = DataElement.build(website.getName(),  mapping, advertisementDom) 

     if dataElement.getValue() :
         if not dataElement.fill(browser):
             sys.stderr.write("\tError occured while attempting to write " + dataElement.getTagName() + " to website " + website.getName() + os.linesep)
         time.sleep(DataElement.FILL_FREEZETIME)

#if dataElement:
#    dataElement.submit(browser)

# \todo : adapt subdir when looping
subdir = args.directory

if DataElement.WebFiller(website.getName(), website.getSuccessElement()).checkVisibility(browser):
    print "Successfully posted advertisement for " + subdir + "."
    try:
        browser.quit()
    except OSError as e:
        #print "(Catched OSError : " + str(e) + ".)"
        a = []
else:
    print "It seems that errors occurent posting advertisement for " + subdir + ". Browser was not closed."
