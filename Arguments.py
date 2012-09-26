import argparse

## \brief Create an argparse.ArgumentParser instance and make it publicly available in the parser data member.
# The argument parser is already aware of two common arguments : <i>directory</i> and <i>--websites</i>.
class Arguments(object):
    def __init__(self, programDescription):
        self.parser = argparse.ArgumentParser(description=programDescription)
        self.parser.add_argument("directory", type=unicode, help="The top directory containing the advertisements' directories.")
        self.parser.add_argument("-w", "--websites", type=unicode, nargs='+', required=True, help="Websites to which the advertisement will be linked.")

