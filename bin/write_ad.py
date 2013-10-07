#!/bin/python

from agilister import fillers, config, website, arguments

from xml.dom.minidom import parse
import os
import sys


def get_ads_files(directory):
    single_ad = os.path.join(directory, config.ADVERTISEMENT_FILE)
    if os.path.exists(single_ad):
        return [single_ad]
        
    return [ad_file for ad_file in [os.path.join(directory, subdir, config.ADVERTISEMENT_FILE)
                                    for subdir in config.get_subdirs(directory)]
            if os.path.exists(ad_file)]


def update_ads_for_website(website_details, ad_list):
    for field in args.fields:
        update_ads_field(website_details, field, ad_list)


def update_ads_field(website_details, data_field_tagname, ad_list):
    map_element = website_details.get_data_mapping(data_field_tagname)
    if not map_element:
        sys.stderr.write("Cannot find the mapping for field " + data_field_tagname
                         + " in website " + website_details.getName() + ".")
        sys.exit(-2)

    for advertisement_data_file in ad_list:
        data_dom = parse(advertisement_data_file)
        dom_feeder = fillers.DomDataFeeder(website_details.get_name(),
                                           map_element._xml_element, data_dom)
        field_choices = website_details.get_data_tag_choices(data_field_tagname)

        banner = "## " + advertisement_data_file + " ## : " + data_field_tagname
        new_value = field_choices.prompt_user(banner, dom_feeder.get_value())

        if new_value:
            dom_feeder.set_value(new_value)
            f = open(advertisement_data_file, "w")
            f.write(data_dom.toxml("utf-8"))
            f.close()
        else:
            print "Value was NOT changed."


if __name__ == "__main__":
    parser = arguments.Arguments("Write advertisements.").parser
    parser.add_argument("fields", metavar="field", type=unicode, nargs='+',
                        help="A field that will be written in the advertisements.")
    args = parser.parse_args()

    ad_list = get_ads_files(args.directory)
    map(lambda website: update_ads_for_website(website, ad_list),
        [website.WebsiteDetails(website_name) for website_name in args.websites])
