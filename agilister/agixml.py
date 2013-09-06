class Tag:
    HANDLERS = u"handlers"
    FIELD_MAP = u"fieldmap"
    PHOTO = u"photo"
    PRECODE = u"precode"
    MAP = u"map"
    ADVERTISEMENT = u"annonce"


class Attribute:
    IFRAME = u"iframe"
    PROPER = u"proper"
    SUBMIT = u"submit"
    TYPE = u"type"
    URL = u"url"
    XPATH = u"xpath"
    MAX_PHOTO = u"max"


def present_attribute(xml_element, attribute_name):
    """Helper method to determine if an attribute is "present" in a xml element
       It allows to emulate flags in xml elements. An attribute is said to be present if it's value is set to 1.
       :param xml_element:, element that will be searched against the attribute
       :param attribute_name:
    """
    return xml_element.getAttribute(attribute_name) == u"1"
