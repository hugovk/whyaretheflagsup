#!/usr/bin/env python
# encoding: utf-8
"""
Scrape'n'tweet when the flags are up
"""
from __future__ import print_function, unicode_literals
from bs4 import BeautifulSoup  # pip install BeautifulSoup4
from selenium import webdriver  # pip install selenium
import argparse
import datetime
import glob
import os
import random
import sys
import twitter
import webbrowser
import yaml

HELSINKI_LAT = 60.170833
HELSINKI_LONG = 24.9375


def timestamp():
    """ Print a timestamp and the filename with path """
    print(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p") + " " +
          __file__)


def flag_reason():

    url = "https://whyaretheflagsup.github.io"

#     driver = webdriver.Chrome()
    driver = webdriver.PhantomJS(service_log_path=os.path.devnull)  # headless
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "lxml")

    # <div class="reason" id="reason"></div>

    reason_div = soup.find_all("span", class_="reason")[0]
    reason = reason_div.text
    if "Flags are not up in Finland today" in reason:
        return None
    return reason


def load_yaml(filename):
    """
    File should contain:
    consumer_key: TODO_ENTER_YOURS
    consumer_secret: TODO_ENTER_YOURS
    access_token: TODO_ENTER_YOURS
    access_token_secret: TODO_ENTER_YOURS
    """
    f = open(filename)
    data = yaml.safe_load(f)
    f.close()
    if not data.viewkeys() >= {
            'access_token', 'access_token_secret',
            'consumer_key', 'consumer_secret'}:
        sys.exit("Twitter credentials missing from YAML: " + filename)
    return data


def build_tweet(reason):
    tweet = "Flags are up in Finland because today is: " + reason

    # An HTTPS link takes 23 characters.
    max = 116 - 1 - 23  # max tweet with image - space - link
    if len(tweet) > max:
        tweet = tweet[:max-1] + "…"

    url = "https://whyaretheflagsup.github.io"
    tweet += " " + url
    return tweet


def random_img(spec):
    """Find images (non-recursively) in dirname"""
    # Get a list of matching images, full path
    matches = glob.glob(spec)
    print("Found", len(matches), "images")

    if not len(matches):
        sys.exit("No files found matching " + spec)

    # Pick a random image from the list
    random_image = random.choice(matches)
    print("Random image:", random_image)
    return random_image


def tweet_it(string, credentials, image=None):
    """ Tweet string and image using credentials """
    if len(string) <= 0:
        return

    # Create and authorise an app with (read and) write access at:
    # https://dev.twitter.com/apps/new
    # Store credentials in YAML file
    t = twitter.Twitter(auth=twitter.OAuth(
        credentials['access_token'],
        credentials['access_token_secret'],
        credentials['consumer_key'],
        credentials['consumer_secret']))

    print("TWEETING THIS:\n", string)

    if args.test:
        print("(Test mode, not actually tweeting)")
    else:

        if image:
            print("Upload image")

            # Send images along with your tweets:
            # First just read image from the web or from files the regular way
            with open(image, "rb") as imagefile:
                imagedata = imagefile.read()
            # TODO dedupe auth=OAuth(...)
            t_up = twitter.Twitter(domain='upload.twitter.com',
                                   auth=twitter.OAuth(
                                       credentials['access_token'],
                                       credentials['access_token_secret'],
                                       credentials['consumer_key'],
                                       credentials['consumer_secret']))
            id_img = t_up.media.upload(media=imagedata)["media_id_string"]
        else:
            id_img = None  # Does t.statuses.update work with this?

        result = t.statuses.update(
            status=string,
            lat=HELSINKI_LAT, long=HELSINKI_LONG,
            display_coordinates=True,
            media_ids=id_img)
        url = "http://twitter.com/" + \
            result['user']['screen_name'] + "/status/" + result['id_str']
        print("Tweeted:\n" + url)
        if not args.no_web:
            webbrowser.open(url, new=2)  # 2 = open in a new tab, if possible


if __name__ == "__main__":

    timestamp()

    parser = argparse.ArgumentParser(
        description="Scrape'n'tweet when the flags are up",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-y', '--yaml',
        default='/Users/hugo/Dropbox/bin/data/whyaretheflagsup.yaml',
        help="YAML file location containing Twitter keys and secrets")
    parser.add_argument(
        '-i', '--image',
        # TODO directory/spec. See randimgbot.py
        default='/Users/hugo/Dropbox/bin/data/finnishflags/flag*',
        help="Path to an image of a flag to upload")
    parser.add_argument(
        '-nw', '--no-web', action='store_true',
        help="Don't open a web browser to show the tweeted tweet")
    parser.add_argument(
        '-x', '--test', action='store_true',
        help="Test mode: go through the motions but don't tweet")
    args = parser.parse_args()

    reason = flag_reason()
    if not reason:
        sys.exit("Flags are (probably) not up")

    print("Flags are up!")
    print(reason)

    tweet = build_tweet(reason)

    twitter_credentials = load_yaml(args.yaml)

    print("Tweet this:\n", tweet)
    image = random_img(args.image)
    tweet_it(tweet, twitter_credentials, image)

# End of file
