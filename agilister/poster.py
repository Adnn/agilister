from xml.dom.minidom import parse, parseString
import time
import os
import re
import logging

from selenium import webdriver

import config
import fillers
from agixml import Tag, Attribute


def merge_data(xml_ordered_list):
    """The merging order will define the precedence of the files (in case of duplicate element)
    """
    xmlMerge = u'<?xml version="1.0" encoding="utf-8"?><merge></merge>'
    dom_merge = parseString(xmlMerge)
    for xml_file in xml_ordered_list:
        if xml_file is not None and os.path.exists(xml_file):
            dom_merge.firstChild.appendChild(parse(xml_file).firstChild)
        else:
            logging.warning("A file to be merged cannot be found.")
    return dom_merge

class AbstractHandler(object):
    """An interface for handlers callbacks.
       Handlers are listed in the website_detail-settings.xml, and each type can be associated to a different subclass of this one.
       The subclass implements an handle(handler_node) method which realize the desired behavior.
    """
    def __init__(self, browser):
        self.browser = browser

    def handle(self, precode_node):
        """The abstract method to be implemented by deriving classes"""
        raise NotImplementedError

class PrecodeHandler(AbstractHandler):
    """ Execute the code contained as text by the given node """
    def handle(self, precode_node):
        precode = precode_node.firstChild.nodeValue
        if precode:
                exec precode

class PhotoHandler(AbstractHandler):
    """ Handle the posting of picture described by the node
        This handler list the files whose name is a number with extension .JPG or .jpg
        Then post them in ascending order."""
    def __init__(self, browser, data_dir):
        super(PhotoHandler, self).__init__(browser)
        self._data_dir = data_dir

    def handle(self, photo_node):
        images = [f for f in os.listdir(self._data_dir) if re.match(r'[0-9]+\.(JPG|jpg)', f)]

        try:
            max_photos = int(photo_node.getAttribute(Attribute.MAX_PHOTO))
        except ValueError:
            max_photos = len(images)

        for image_file, image_id in zip(images, range(max_photos)):
            fillers.PhotoFiller(photo_node,
                                os.path.join(self._data_dir, image_file)).fill(self.browser)
            time.sleep(config.FILL_FREEZETIME)

class FieldsHandler(AbstractHandler):
    """ Handle filling out the fields, following the mappings contained by the node """
    def __init__(self, browser, data_dom, website_name):
        super(FieldsHandler, self).__init__(browser)
        self.data_dom = data_dom
        self.website_name = website_name

    def handle(self, fieldmap_node):
        for mapping in fieldmap_node.getElementsByTagName(Tag.MAP):
            data_element = fillers.build_filler(self.website_name, mapping, self.data_dom)

            if data_element.get_feeder_value():
                if not data_element.fill(self.browser):
                    logging.warning("\tError occurred while attempting to write "
                                    + mapping.firstChild.nodeValue + " to website_detail "
                                    + self.website_name + os.linesep)
                time.sleep(config.FILL_FREEZETIME)

def post(website_action, data_dom, data_dir):
    """The generic function to complete a given website action, using the default handlers
       Input data is given in the form of the merged dom 'data_dom'
    """
    browser = webdriver.Chrome()
    browser.get(website_action.get_url())

    filler_callbacks = {Tag.FIELD_MAP: FieldsHandler(browser,
                                                     data_dom,
                                                     website_action.website_details.get_name()),
                        Tag.PHOTO:     PhotoHandler(browser,
                                                    data_dir),
                        Tag.PRECODE:   PrecodeHandler(browser),}

    [filler_callbacks[filler.tagName].handle(filler)
        for filler in website_action.get_next_handler()]

    if fillers.WebFiller(website_action.get_success_element()).check_visibility(browser):
        try:
            browser.quit()
        except OSError as e:
            #print "(Caught OSError : " + str(e) + ".)"
            pass
        return True
    else:
        return False



