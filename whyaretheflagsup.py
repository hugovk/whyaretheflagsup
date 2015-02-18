#!/usr/bin/env python
# encoding: utf-8
"""
Scrape'n'tweet when the flags are up
"""
from __future__ import print_function
import argparse
from bs4 import BeautifulSoup  # pip install BeautifulSoup4
from selenium import webdriver  # pip install selenium
import sys
import twitter
import webbrowser
import yaml

HELSINKI_LAT = 60.170833
HELSINKI_LONG = 24.9375


def flag_reason():

    url = "https://whyaretheflagsup.github.io"

    # driver = webdriver.Chrome()
    driver = webdriver.PhantomJS()  # headless
    driver.get(url)
    soup = BeautifulSoup(driver.page_source)

    # <div class="reason" id="reason"></div>

    reason_div = soup.find_all("div", class_="reason")[0]
    reason = reason_div.text
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
    tweet = "Flags are up in Finland because today is: " + str(reason)

    # An HTTP link takes 22 characters.
    max = 140 - 1 - 22  # max tweet - space - link
    if len(tweet) > max:
        tweet = tweet[:max-1] + "…"

    url = "http://whyaretheflagsup.github.io"
    tweet += " " + url
    return tweet


def tweet_it(string, credentials):
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
        result = t.statuses.update(
            status=string,
            lat=HELSINKI_LAT, long=HELSINKI_LONG,
            display_coordinates=True)
        url = "http://twitter.com/" + \
            result['user']['screen_name'] + "/status/" + result['id_str']
        print("Tweeted:\n" + url)
        if not args.no_web:
            webbrowser.open(url, new=2)  # 2 = open in a new tab, if possible


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape'n'tweet when the flags are up",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-y', '--yaml',
        default='/Users/hugo/Dropbox/bin/data/whyaretheflagsup.yaml',
        help="YAML file location containing Twitter keys and secrets")
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
    tweet_it(tweet, twitter_credentials)

# End of file
