import os

ADVERTISEMENT_FILE = u"annonce.xml"
AGILISTER_ENVAR = u"AGILISTER"
WEB_FOLDER = u"websites"
USER_FOLDER = u"users"

""" Time to wait after filling a web element and before filling the next """
ELEMENT_TIMEOUT = 10

FILL_FREEZETIME = 1

""" The directory containing all metadata folders.
    Edit this value only if you moved them away from the install folder.
    You can alternatively use the 'AGILISTER' environment variable.
"""
_AGILISTER_PATH = None


def agilister_path():
    """ :return: Agilister install folder (supposed to contain metadata folders)
    """
    global _AGILISTER_PATH
    if _AGILISTER_PATH is None:
        try:
            _AGILISTER_PATH = os.environ[AGILISTER_ENVAR]
        except KeyError:
            _AGILISTER_PATH = os.path.dirname(os.path.dirname(__file__))
    return _AGILISTER_PATH


def user_file(user_name):
    user_file = os.path.join(agilister_path(), USER_FOLDER, user_name+".xml")
    if os.path.exists(user_file):
        return user_file
    return None


def get_subdirs(dir):
    """Return a list of the sub directories in 'dir',
       as paths starting with dir"""
    return [name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]


