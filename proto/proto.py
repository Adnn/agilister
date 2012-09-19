from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

driver = webdriver.Chrome()
driver.get("http://post.vivastreet.fr")
input = driver.find_element_by_name("detail")

from xml.dom.minidom import parse, parseString
dom = parse("./proto-annonce.xml")
text = dom.firstChild.childNodes[7].firstChild.nodeValue
print type(text)
input.send_keys(text)
