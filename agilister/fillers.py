from feeders import DummyDataFeeder, DomDataFeeder
from agixml import Attribute, present_attribute
import config

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

TYPE_SELECT = u"select"
TYPE_TEXT = u"text"
TYPE_RADIO = u"radio"
TYPE_CHECKBOX = u"checkbox"


def visible(element):
    """Callback method for WebDriverWait.until() allowing to determine if a web page element is currently displayed
       :param element: Web element to be checked for visibility
       :return: the element if it is displayed, None otherwise
    """
    if element.is_displayed():
        return element
    return None


def remove_endl(base_string):
    """Remove Dos and Unix end of lines from a string, without replacing them.
    """
    return base_string.replace("\r\n", "\n").replace("\n", "")


def remove_tab(base_string):
    """Remove tabulations from a string, without replacing them.
    """
    return base_string.replace("\t", "")


class WebFiller(object):
    """An abstract class whose interface defines the ability to fill a Web element,
       independently from the source of data for the web element.
       The element that will be filled is described by a relation_element (xml) provided at construction.
       Subclasses can be implemented for different web elements,
       they have to implement the _fill_impl() method.
       It is decoupled from the data source, which should be a 'DataFeeder' given on construction.

       :param relation_element: An xml element, containing at least a 'xpath' attribute that uniquely
                                identifies a web element on the current browser page.
       :param data_feeder: an object providing a get_value() method that can be used by subclasses
                           as a source for the data used to fill the web element.
    """
    def __init__(self,
                 #website_action,
                 relation_element,
                 data_feeder=None):
        self.relation_element = relation_element

        # \todo : cleanup members
        #self._website_name = website_detail
        #self._website_action = website_action
        ## XPath to the Web element to be filled.
        self._web_xpath = relation_element.getAttribute(Attribute.XPATH)
        ## iframe containing the Web element.
        self._iframe = relation_element.getAttribute(Attribute.IFRAME)
        ## Should we submit() the Web element once filled
        self._submit_flag = present_attribute(relation_element, Attribute.SUBMIT)
        self._data_feeder = data_feeder

    def get_feeder_value(self):
        """Just forward the call to the data feeder.
           It is a good idea for subclasses to use this method as a way to obtain the data
        """
        return self._data_feeder.get_value()

    def fill(self, webDriver):
        """Part of public interface : clients ask for the web element tied to this 'WebFiller'
           to be filled by calling this method
        """
        return self._web_element_operation(webDriver, self._fill_operation)

    def check_visibility(self, webDriver):
        """Part of the public interface :
           the method returns True if the pointed Web element is displayed on the web page,
           False if it is sill not visible after the defined timeout.
        """
        return self._web_element_operation(webDriver, None)

    def _web_element_operation(self, web_driver, operation):
        """A wrapper to call any operation on a Web element if it is found.
           It switches to the web element iframe (if necessary), wait for it to be visible,
           then call the provided operation on it.
           :return: True if the element was found, False otherwise.
        """
        if self._iframe:
            web_driver.switch_to_frame(self._iframe)

        try:
            input_element = WebDriverWait(web_driver, config.ELEMENT_TIMEOUT).until(
                lambda d: visible(web_driver.find_element(By.XPATH, self._web_xpath)))
            if operation:
                operation(input_element)
        except TimeoutException:
            return False
        finally:
            if self._iframe:
                web_driver.switch_to_default_content()

        return True

    def _fill_operation(self, input_element):
        """A proxy to '_fill_impl', that is only responsible for submitting the element
           if the flag is present in the relation_element.
        """
        self._fill_impl(input_element)
        if self._submit_flag:
            input_element.submit()

    def _fill_impl(self, input_element):
        """This method has to be implemented by derived classes.
           It is responsible for the realization of the web element filling logic.
        """
        raise NotImplementedError


class PhotoFiller(WebFiller):
    """A WebFiller specialised for image files.
       It was designed for Vivastreet simple "input-file" button
       and works with LeBonCoin thanks to the submit flag.
    """
    def __init__(self, photo_element, photo_file):
        """Ctor
           :param photo_element: the xml relation element describing the Web photo element of website_detail
           :param photo_file: a string giving the absolute path to the image on the local filesystem
        """
        super(PhotoFiller, self).__init__(photo_element,
                                          DummyDataFeeder(photo_file))

    def _fill_impl(self, input_element):
        input_element.send_keys(self.get_feeder_value())


class SelectElement(WebFiller):
    """Refinement of DataElement for select Web elements.
       For a select, the value found in the data DOM defines the select's option's value to be selected.
    """
    def __init__(self, website_name, map_element, data_dom):
        super(SelectElement, self).__init__(map_element,
                                            DomDataFeeder(website_name, map_element, data_dom))
        self._web_type = TYPE_SELECT

    def _fill_impl(self, input_element):
        Select(input_element).select_by_value(self.get_feeder_value())


class TextElement(WebFiller):
    """Refinement of DataElement for free text Web elements.
       For a free text element, the value found in the data DOM is set as text input.
       The newlines are removed if the free text is not a textarea.
    """
    def __init__(self, website_name, map_element, data_dom):
        super(TextElement, self).__init__(map_element,
                                          DomDataFeeder(website_name, map_element, data_dom))
        self._web_type = TYPE_TEXT

    def _fill_impl(self, input_element):
        value = self.get_feeder_value()
        if input_element.tag_name != u'textarea':
            value = remove_endl(value).strip()
        value = remove_tab(value)
        input_element.send_keys(value)


class RadioElement(WebFiller):
    """Refinement of DataElement for radio Web elements.
       For a radio element, the value found in the dataDOM is the XPath defining which radio box should be checked. Thus the XPath found in the map_element is not necessarily pointing to the exact element to check.
    """
    def __init__(self, website_name, map_element, data_dom):
        super(RadioElement, self).__init__(map_element,
                                           DomDataFeeder(website_name, map_element, data_dom))
        self._web_type = TYPE_RADIO
        self._web_xpath = self.get_feeder_value()

    def _fill_impl(self, input_element):
        input_element.click()


class CheckboxElement(WebFiller):
    def __init__(self, website_name, map_element, data_dom):
        super(CheckboxElement, self).__init__(map_element,
                                              DomDataFeeder(website_name, map_element, data_dom))
        self._web_type = TYPE_CHECKBOX

    def _fill_impl(self, input_element):
        should_select = (self.get_feeder_value().upper() == "Y")
        if input_element.is_selected() != should_select:
            input_element.click()


def build_filler(website, map_element, data_dom):
    """Factory of DataElements, returning the correct final class instance depending on the type of Web element that the map_element is pointing to.
    """
    type_ = map_element.getAttribute("type")
    if type_ == TYPE_SELECT:
        return SelectElement(website, map_element, data_dom)
    if type_ == TYPE_RADIO:
        return RadioElement(website, map_element, data_dom)
    if type_ == TYPE_CHECKBOX:
        return CheckboxElement(website, map_element, data_dom)
    else:
        return TextElement(website, map_element, data_dom)

# \todo : restore this functionality
# def build_filler_from_tag(website, data_field_tagname, data_dom):
#     """Factory of DataElements, determining which map element to use based on the desired data DOM tagame.
#     """
#     map_element = website.getMapping(data_field_tagname)
#     if map_element:
#         return build_filler(website.get_name(), map_element, data_dom)
#     else:
#         return None
