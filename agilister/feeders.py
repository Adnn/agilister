from agixml import Attribute, Tag, present_attribute

class DataFeeder(object):
    """Abstract class, with the responsibility to generate the data that should be used to fill
       a website_details element.
       It allows decoupling the value generation from the actual filling operation.
    """
    pass

    def get_value(self):
        raise NotImplementedError

class DummyDataFeeder(DataFeeder):
    """The simplest kind of 'DataFeeder' : feed a value given at the object construction.
    """
    def __init__(self, value):
        self._value = value

    def get_value(self):
        return self._value

class DomDataFeeder(DataFeeder):
    """A DataFeeder specialization for values found in a data DOM.
       Those data DOM list different values inside different tag pairs,
       whose tagname describe the content.
       Site agnostic content is found as a text element at first level inside the tag pairs.
       Site specific content is enclose in an extra tag pair whose tagname is the website_detail name.
    """

    def __init__(self, website_name, map_element, data_dom):
        """Ctor
           :param map_element: is the xml relation_element. In addition to a relation_element,
                               it contains a child text element giving the name of the tag
                               containing the data (in data_dom).
           :param data_dom: the xml document listing the different fields value
                            inside separate tag pairs.
        """
        self.data_dom = data_dom
        self._field_tag = map_element.firstChild.nodeValue
        self._field_proper = present_attribute(map_element, Attribute.PROPER)
        self._field_element = None
        self._website_name = website_name

    def get_tagname(self):
        """ Returns the tagname from data_dom associated to the pointed Web element"""
        return self._field_tag

    def get_value(self):
        """ Current value associated to the Web element (as found in the data DOM)"""
        self._get_field_element()
        if self._field_element:
            return self._field_element.firstChild.nodeValue
        else:
            return None

    def set_value(self, newValue):
        """ Update/Create the value in the data DOM"""
        self._get_field_element(create=True)

        text_value_node = self._field_element.firstChild
        if text_value_node:
            text_value_node.nodeValue = newValue
        else:
            text_value_node = self.data_dom.createTextNode(newValue)
            self._field_element.appendChild(text_value_node)

    # \todo : delete
    # def get_type(self):
    #     """ Type of the Web element"""
    #     return self._web_type

    def _get_field_element(self, create=False):
        """Private method to get, and eventually create,
           the element from the data DOM that is pointed by map_element.
           It is responsible for implementing correct site agnostic / site specific data look-up.
        """
        # /todo : rework logic
        if not self._field_element:
            ad_element = self.data_dom.getElementsByTagName(Tag.ADVERTISEMENT)[0]
            try:
                general_element = self.data_dom.getElementsByTagName(self._field_tag)[0]
            except IndexError:
                if not create:
                    return
                general_element = self.data_dom.createElement(self._field_tag)
                ad_element.appendChild(general_element)

            if not self._field_proper:
                self._field_element = general_element
                return

            try:
                proper_element = general_element.getElementsByTagName(self._website_name)[0]
            except IndexError:
                if not create:
                    return
                proper_element = self.data_dom.createElement(self._website_name)
                general_element.appendChild(proper_element)

            self._field_element = proper_element

