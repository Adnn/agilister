from xml.dom.minidom import parse
from xml.dom import Node
import urllib2
from lxml import etree
import os
from agilister.agixml import present_attribute

import fillers
from agixml import Tag, Attribute
import config

class Choices(object):
    """Abstract class to represent the different choices to fill a data element
       (in the data DOM) based on the type of web element it will be linked to
       in a given website_detail.

       For example if a data element is linked to a select web element,
       the only choices for it's values would be the nested option's values.
    """

    def prompt_user(self, banner, current_value):
        """This method handles communication with the user so he can select a value for the data element.
           It has to be implemented for concrete derived classes.
        """
        raise NotImplementedError

class SelectChoices(Choices):
    """Specialization of Choices for select web elements.
    """
    def __init__(self, prompt_text, value_list):
        self._prompt_text = prompt_text
        self._value_list = value_list

    def get_value(self, value_id):
        """The value of the valueId(th) option (0 indexed)
        """
        return self._value_list[value_id]
    
    def get_index(self, value):
        return self._value_list.index(value)

    def prompt_user(self, banner, current_value):
        print self._prompt_text
        if not current_value:
            current_value=""
        else:
            current_value=str(self.get_index(current_value))
        try:
            print banner
            option_id = int(raw_input("Enter new value[" + current_value + "] : "))
            new_value = self.get_value(option_id)
        except (ValueError, IndexError):
            new_value = None

        return new_value

class TextChoices(Choices):
    """Specialization of Choices for free text web elements.
    """
    def __init__(self, prompt_text):
        self._prompt_text = prompt_text

    def prompt_user(self, banner, current_value):
        print self._prompt_text
        if not current_value:
            current_value=""
            
        print banner
        new_value = raw_input("Enter new value[" + current_value + "] : ")

        if len(new_value) == 0:
            new_value = None

        return new_value

class MapElement(object):
    def __init__(self, map_xml_element, website_action):
        self._xml_element = map_xml_element
        self.website_action = website_action

    def tag_name(self):
        return self._xml_element.firstChild.nodeValue

    def xpath(self):
        return self._xml_element.getAttribute(Attribute.XPATH)

    def type(self):
        return self._xml_element.getAttribute(Attribute.TYPE)

    def is_proper(self):
        return present_attribute(self._xml_element, Attribute.PROPER)

class WebsiteAction(object):
    _element = None
    _handlers_list = None
    website_details = None

    def get_url(self):
        """return the url the browser has to point to before starting to fill the forms"""
        return self._element.getAttribute(Attribute.URL)

    def get_next_handler(self):
        """ Obtain the next filler element, in order of appearance in the xml """
        if self._handlers_list is None:
            handlers_element = self._element.getElementsByTagName(Tag.HANDLERS).item(0)
            if handlers_element:
                self._handlers_list = handlers_element.childNodes
            else:
                self._handlers_list = []


        for handler in self._handlers_list:
            if handler.nodeType == Node.ELEMENT_NODE:
                yield handler

    def get_success_element(self):
        """Return an xml element describing a successful post consequence.
           It could in particular contain a XPath attribute defining a web element
           that becomes visible when posting completes successfully.
        """
        return self._element.getElementsByTagName("success").item(0)

    def _get_map_elements(self, data_tag_name):
        # with lxml : tree.xpath("./*/*/fieldmap/map[text()=data_tag_name]")
        #getElementsByTagName is looking for children at any depth
        map_elements = (MapElement(xml_map_element, self) for xml_map_element
                        in self._element.getElementsByTagName(Tag.MAP))
        return (filtered_map for filtered_map in map_elements
                if filtered_map.tag_name() == data_tag_name)


class WebsiteDetails(object):
    """A wrapper around Website metadata that is found in 'sitename.xml' file.
       It gives access to the different fields found in the metadata,
       through getters that are the centralized place knowing about the DOM structure.
       It delegate the 'handlers' xml element to the 'WebsiteAction' wrapper.
    """
    def __init__(self, website_name):
        """Ctor
           :param website_name: The website_detail name for which the metadata should be loaded.
           The code will look in the default websites directory ($AGILISTER/websites)
           for the file <i>website_name</i>.xml
        """
        website_file = WebsiteDetails.get_file(website_name)
        if website_file:
            self._dom = parse(website_file)
        else:
            raise Exception("Cannot find the website_detail " + website_name + ".")
        self._name = website_name

        self._actions = None
        self._data_tag_to_map_element = {}
        #self._generate_data_tag_dictionnary()

    # """Initializes a dictionary that will map each data tagname
    #   (the tagnames in the data DOM) present in the website_detail file,
    #   to the mapElement (relationElement) listing it.
    #  It then looks like {dataTagname : {"map":mapElement}}.
    # # The dictionary value element is a nested dictionary,
    #  so it is possible to attach additional information to each data tagname.
    # """
    # def _generate_data_tag_dictionnary(self):
    #     self._data_tag_to_map_element= {}
    #     for mapping in self.getMappings():
    #         self._data_tag_to_map_element[mapping.firstChild.nodeValue] = {"map" : mapping}

    def get_name(self):
        """ Return the website name"""
        return self._name

    def get_action(self, action_name):
        """Return a WebsiteAction for the given tag name.
           The dictionary of 'WebsiteActions' is lazily initialized on first call
        """
        return self._actions_access()[action_name]

    def get_data_mapping(self, data_tagname):
        """Return the (first) map element corresponding to the given data_tagname
        """
        if not data_tagname in self._data_tag_to_map_element:
            self._data_tag_to_map_element[data_tagname] =\
                {"map": tuple([map_element
                              for key, website_action in self._actions_access().iteritems()
                              for map_element in website_action._get_map_elements(data_tagname)])}

        map_tuple = self._data_tag_to_map_element[data_tagname]["map"]
        if map_tuple:
            #return the first element in the tuple
            return map_tuple[0]
        else:
            return None

    def get_website_datafile(self):
        """Return the xml file with website_detail specific data if it exists"""
        dataFile = os.path.join(config.agilister_path(), config.WEB_FOLDER,
                                self._name+"-data.xml")
        if os.path.exists(dataFile):
            return dataFile
        else:
            return None

    @staticmethod
    def get_file(website_name):
        website_file = os.path.join(config.agilister_path(), config.WEB_FOLDER, website_name+".xml")
        if os.path.exists(website_file):
            return website_file
        else:
            return None

    def _actions_access(self):
        if not self._actions:
            self._initialize_actions()
        return self._actions

    def _initialize_actions(self):
        """Lazy initializer for all the actions in this website"""
        self._actions = {}
        for action_element in [node for node in self._dom.firstChild.childNodes
                               if node.nodeType == Node.ELEMENT_NODE]:
            website_action = WebsiteAction()
            website_action._element = action_element
            website_action.website_details = self
            self._actions[action_element.tagName] = website_action
    # ## \return The website_detail post url (i.e. the first page of the posting form)
    # def getPostUrl(self):
    #     return self._dom.firstChild.getElementsByTagName("url").item(0).getElementsByTagName("post").item(0).firstChild.nodeValue
    #
    # ## \return A string containing Python code that should be executed when the post url is loaded, <b>before</b> any attempt to fill web elements.
    # def getPrecode(self):
    #     precodeElem = self._dom.firstChild.getElementsByTagName("precode").item(0)
    #     if precodeElem:
    #         return precodeElem.firstChild.nodeValue
    #     return None
    #
    # ## \return the complete <map> xml element, containing the nested <mapping> elements.
    # def getMappings(self):
    #     return self._dom.firstChild.getElementsByTagName("fieldmap").item(0).getElementsByTagName("map")
    #
    # ## \return A single <mapping> xml element, which is a kind of relationElement referred as mapElement in the documentation.
    # # The returned element is mapping a web element (defined by its XPath) to a data DOM tagname (meaning this tag contains the data to fill the pointed web element).
    # def getMapping(self, dataFieldTagName):
    #     if dataFieldTagName in self._data_tag_to_map_element:
    #         return self._data_tag_to_map_element[dataFieldTagName]["map"]
    #     else:
    #         return None
    #
    # ## \return The <photo> xml element, which is a relationElement referred as photoElement in the documentation.
    # # The returned photoElement describes how to post images when posting on the website_detail.
    # def getPhotoElement(self):
    #     return self._dom.firstChild.getElementsByTagName("photo").item(0)
    #
    def get_data_tag_choices(self, tag_name):
        """:return: the Choices instance corresponding to the given data tag name.
           If the Choices instance was not already generated,
            it is and then attached to the corresponding dataTag value,
            as a dictionary entry with the key "choices".
            Dictionary looks like {tagname : {"map" : (MapElement,...),
                                              "choices" : choicesInstance[, ...]}}
        """
        if self.get_data_mapping(tag_name):
            if "choices" in self._data_tag_to_map_element[tag_name]:
                return self._data_tag_to_map_element[tag_name]["choices"]
            else:
                return self._generate_choices(tag_name)
        else:
            return None

    def _generate_choices(self, tag_name):
        """Factory method for Choices,
           instantiating the correct specialization corresponding to the web element linked to the given tagname.
        """
        mapping = self.get_data_mapping(tag_name)
        output = u""
        option_list = []

        postPage = urllib2.urlopen(mapping.website_action.get_url())
        html_parser = etree.HTMLParser()
        webpage_tree = etree.parse(postPage, html_parser)

        if mapping.type() == fillers.TYPE_SELECT:
            select = webpage_tree.xpath(mapping.xpath())[0]
            selectorId = 0
            for option in select:
                if option.get("disabled"):
                    output += option.text + os.linesep
                elif option.get("value"):
                    output += "\t" + str(selectorId) + " : " + option.text + os.linesep
                    option_list.append(option.get("value"))
                    selectorId += 1

            choices = SelectChoices(output, option_list)
        elif mapping.type() == fillers.TYPE_RADIO:
            # \todo : Implement radio choices
            raise NotImplemented("Choices for radio not implemented yet.")
        else:
            choices = TextChoices(output)

        self._data_tag_to_map_element[tag_name]["choices"] = choices
        return choices
