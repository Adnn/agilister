import urllib2
from lxml import etree
from xml.dom.minidom import parse, parseString
import argparse
import os, sys
import DataElement
import WebsiteDetails
import Arguments

def get_subdirs(dir):
        return [name for name in os.listdir(dir)
                            if os.path.isdir(os.path.join(dir, name))]

def updateAdsForWebsite(website, advertisementList):
    websiteFile = os.path.join(os.environ['AGILISTER'], DataElement.WEB_FOLDER, website.getName()+".xml")
    if(os.path.exists(websiteFile)) :
            domWeb = parse(websiteFile)
    else :
        sys.stderr.write("Cannot find the website " + website + ".")
        sys.exit(-1)

    for field in args.fields:
        updateAdsField(website, field, advertisementList)

def updateAdsField(website, dataFieldTagName, advertisementList):
    fieldMap = website.getMapping(dataFieldTagName) 
    if not fieldMap:
        sys.stderr.write("Cannot find the mapping for field " + dataFieldTagName + " in website " + website.getName() + ".")
        sys.exit(-2)

    for advertisementDataFile in advertisementList:
        dataDom = parse(advertisementDataFile)
        fieldElement = DataElement.build(website.getName(), fieldMap, dataDom)
        fieldChoices = website.getDataTagChoices(dataFieldTagName)

        banner = "## " + advertisementDataFile + " ## : " + dataFieldTagName
        newValue = fieldChoices.promptUser(banner, fieldElement.getValue())


        if newValue:
            fieldElement.setValue(newValue)

            f = open(advertisementDataFile, "w")
            f.write(dataDom.toxml("utf-8"))
            f.close()
        else:
            print "Value was NOT changed."



parser = Arguments.Arguments("Write advertisements.").parser
parser.add_argument("fields", metavar="field", type=unicode, nargs='+', help="A field that will be written in the advertisements.")
args = parser.parse_args()

website = WebsiteDetails.WebsiteDetails(args.websites[0])
adList = [] 
for subdir in get_subdirs(args.directory):
    advertisementDataFile = os.path.join(args.directory, subdir, DataElement.ADVERTISEMENT_FILE)
    if(os.path.exists(advertisementDataFile)) :
        adList.append(advertisementDataFile)

updateAdsForWebsite(website, adList)
