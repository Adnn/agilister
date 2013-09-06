#!python
import os
import sys
import logging
import time

from agilister import poster, config
from agilister import arguments
from agilister.website import WebsiteDetails

import write_ad


NEXT_POST_COOLDOWN = 100
def post_ad_on_websites(ad_file, user_file, websites, action, sleep_time=[0]):
    """Post a single ad on each website is the given list
       :param sleep_time: It is automatically used to store the sleep duration before the next post loop.
                          You should not give it an explicit value.
    """
    time.sleep(sleep_time[0])
    start = time.time()
    map(lambda website: post_ad(ad_file, user_file, website, action), websites)
    stop = time.time()

    sleep_time[0] = NEXT_POST_COOLDOWN - (stop-start)


def post_ad(ad_file, user_file, website, action):
    """ Post a single ad on a single website_details
    """
    ad_dir = os.path.dirname(ad_file)
    ad_subdir = os.path.basename(os.path.normpath(ad_dir))

    print os.linesep + "### " + ad_subdir + "(" + website.get_name() + ") ###"
    merged_ad_dom = poster.merge_data((ad_file, website.get_website_datafile(), user_file))

    if poster.post(website.get_action(action), merged_ad_dom, ad_dir):
        print "Successfully posted advertisement for " + ad_subdir + "."
    else:
        print "It seems that errors occurred posting advertisement for " + ad_subdir \
              + ". Browser was not closed."


if __name__ == "__main__":
    parser = arguments.Arguments("The advertisement poster."
                                 " It will look for ad subdirs, and merge the ad specific data"
                                 " with user data and website data.").parser
    parser.add_argument("-u", "--user", type=unicode, required=True,
                        help="The user on whose behalf the advertisements will be posted.")
    parser.add_argument("-a", "--action", type=unicode, required=False, default="posting",
                        help="The action to execute on this website.")
    args = parser.parse_args()

    user_file = config.user_file(args.user)
    if not user_file:
        logging.error("Cannot find the user file for " + args.user + ".")
        sys.exit(-1)

    map(lambda ad_file: post_ad_on_websites(ad_file, user_file,
                                            [WebsiteDetails(website_name)
                                            for website_name in args.websites],
                                            args.action),
        write_ad.get_ads_files(args.directory))
