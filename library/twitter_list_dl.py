#!/usr/bin/env python
import datetime
import os
from pathlib import Path

import requests
import re
import json
import argparse
import urllib.parse

"""
Usage:
    tweet_url = "https://twitter.com/TwitterDev"
    output = 'D:/output'
    mediaViewer = TwitterMediaViewer(user_home_url = tweet_url, output_dir = output)
    tweets = mediaViewer.get_tweets_from_twitter()
    video_list = mediaViewer.filter_tweets_video(tweets)

    video_links = []
    for video in video_list:
        twitter_url = video["tweet_url"]
        video_links.append(twitter_url)
"""


class TwitterMediaViewer:

    def __init__(self, user_home_url, output_dir='./output'):
        self.requests = requests.Session()
        self.user_home_url = user_home_url
        self.screen_name = user_home_url.split('/')[3].lower()
        self.output_dir = output_dir
        print("[+] user_home_url = " + user_home_url + ", screen_name = " + self.screen_name)

    """
    True if file exists or download successfully.
    """

    def save_picture(self, picture_url):
        print('\t[+] Picture URL : ' + picture_url)
        try:
            picture_uri = urllib.parse.urlparse(picture_url).path

            if Path.exists(Path(self.output_dir) / picture_uri[1:]) is True:
                return True

            picture_response = self.requests.get(picture_url)
            Path.mkdir(Path(self.output_dir) / picture_uri[1:picture_uri.rindex('/')], parents=True, exist_ok=True)
            with open(Path(self.output_dir) / picture_uri[1:], 'wb') as f:
                f.write(picture_response.content)
            return True
        except IOError:
            print("Error : " + IOError)
            return False

    def get_tweets_from_twitter(self):
        main_js_file_response = self.__get_main_js()
        self.__get_bearer_token(main_js_file_response)
        self.__get_activate_token()
        self.__get_user_id(main_js_file_response)
        if self.user_id == '-1':
            return {}

        users, tweets = self.__get_media_list()

        # store the users into ~/Twitter/lower(<screen_name>/user.json
        users_file_path = Path(self.output_dir) / 'Twitter' / self.screen_name
        Path.mkdir(users_file_path, parents=True, exist_ok=True)
        users_file = str(users_file_path / 'user.json')
        self.__save_data(users_file, json.dumps(users[self.user_id]))
        # store the tweets into ~/Twitter/lower(<screen_name>/tweets/<tweet_id>.json
        tweet_file_path = Path(self.output_dir) / 'Twitter' / self.screen_name / 'tweets'
        Path.mkdir(tweet_file_path, parents=True, exist_ok=True)
        for tweet_id in tweets:
            tweet_file = str(tweet_file_path / (tweet_id + '.json'))
            self.__save_data(tweet_file, json.dumps(tweets[tweet_id]))

        return tweets

    def get_tweets_from_disk(self):
        print('\t[+] Fetching tweets from disk.')
        folder = Path(self.output_dir) / 'Twitter' / self.screen_name / 'tweets'
        if Path.exists(folder) is False:
            return None
        files = os.listdir(folder)
        tweets = {}
        for filename in files:
            try:
                with open(folder / filename, 'r') as f:
                    f.seek(0, 0)
                    lines = f.readlines()
                content = ''
                for line in lines:
                    content += line
                tweets[filename.split('.')[0]] = json.loads(content)
            except:
                print('\t[+] Read Error: ' + str(folder / filename))
        return tweets

    def __save_data(self, file, content):
        with open(file, 'w') as f:
            f.writelines(content)

    def __get_main_js(self):
        req = self.requests
        user_home_url = self.user_home_url

        req.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"})
        user_home_response = req.get(user_home_url).text;

        main_js_pattern = 'https://abs.twimg.com/responsive-web/client-web/main.*.js'
        main_js_file_url = re.findall(main_js_pattern, user_home_response)[0]
        main_js_file_response = req.get(main_js_file_url).text
        return main_js_file_response

    def __get_bearer_token(self, main_js_file_response):
        req = self.requests

        authorization_pattern = '[A-Za-z0-9]+%3D[A-Za-z0-9]+'
        authorization = "Bearer " + re.findall(authorization_pattern, main_js_file_response)[0]
        print('[+] Authorization is : ' + authorization)
        req.headers.update({"Authorization": authorization})

    def __get_activate_token(self):
        req = self.requests
        try:
            res = req.post("https://api.twitter.com/1.1/guest/activate.json")
            print("[+] Activate: " + res.text)
            res_json = json.loads(res.text)
            guest_token = res_json.get('guest_token')
            req.headers.update({'x-guest-token': guest_token})
            print('[+] x-guest-token : ' + guest_token)
        except:
            print('[+] __get_activate_token Errors')

    def __get_user_id(self, main_js_file_response):
        req = self.requests
        screen_name = self.screen_name

        variables_dict = '{"screen_name":"' + screen_name + '","withHighlightedLabel":true}'
        variables_str = 'variables=' + str(variables_dict).replace(' ', '').replace('{', '%7B').replace('\"','%22').replace(':', '%3A').replace(',', '%2C').replace('}', '%7D')
        print("UserByScreenName Param:" + variables_str)
        # user_by_screen_name_prefix_pattern = '\\{queryId:\\"[a-zA-Z]+[-]*_[a-zA-Z0-9]+\\",operationName:\\"ViewerTeams\\",operationType:\\"query\\"\\}'
        user_by_screen_name_prefix_pattern = '\\{queryId:\\"[a-zA-Z0-9_-]+\\",operationName:\\"UserByScreenName\\",operationType:\\"query\\"\\}'
        regular_match_list = re.findall(user_by_screen_name_prefix_pattern, main_js_file_response)
        if len(regular_match_list) <= 0:
            print('[+] Error: could not find Screen Name.')
        user_by_screen_name_prefix = regular_match_list[0]
        user_by_screen_name_prefix = str(user_by_screen_name_prefix).replace("queryId", "\"queryId\"").replace(
            "operationName", "\"operationName\"").replace("operationType", "\"operationType\"")
        print("[+] Find Screen Name JSON : " + user_by_screen_name_prefix)
        user_by_screen_name_prefix_json = json.loads(user_by_screen_name_prefix)
        user_by_screen_name_url = "https://twitter.com/i/api/graphql/" + user_by_screen_name_prefix_json.get("queryId") + "/UserByScreenName?" + variables_str
        print("[+] Requesting URL to get User ID : " + user_by_screen_name_url)
        req.headers.update({"content-type": "application/json"})

        # req.headers.update({"x-twitter-active-user": "yes", "x-twitter-auth-type": "OAuth2Session"})
        user_by_screen_name_response = req.get(user_by_screen_name_url)
        print(user_by_screen_name_response.text)
        user_by_screen_name_json = json.loads(user_by_screen_name_response.text)
        if 'errors' not in user_by_screen_name_json:
            user_id = user_by_screen_name_json.get("data").get("user").get("rest_id")
            print("\t[+] user_id = " + user_id)
            self.user_id = user_id
        else:
            self.user_id = '-1'
            self.error = user_by_screen_name_json.get("errors")[0]
            print("\t[+] " + "code = " + str(user_by_screen_name_json.get("errors")[0].get("code")) + ", message = " +
                  user_by_screen_name_json.get("errors")[0].get("message"))


    def __get_media_list(self):
        print('\t[+] Fetching tweets from Twitter.')

        req = self.requests
        user_id = self.user_id

        count = 20
        count_inc = 20
        twitter_home_url = 'https://api.twitter.com/2/timeline/profile/'
        twitter_media_url = 'https://api.twitter.com/2/timeline/media/'
        next_cursor = ""

        while count > 0:
            twitter_list_url = twitter_media_url
            twitter_list_url += user_id + '.json'
            twitter_list_url += '?include_profile_interstitial_type=1'
            twitter_list_url += '&include_blocking=1'
            twitter_list_url += '&include_blocked_by=1'
            twitter_list_url += '&include_followed_by=11'
            twitter_list_url += '&include_want_retweets=1'
            twitter_list_url += '&include_mute_edge=1'
            twitter_list_url += '&include_can_dm='
            twitter_list_url += '&include_can_media_tag=1'
            twitter_list_url += '&skip_status=1'
            twitter_list_url += '&cards_platform=Web-12'
            twitter_list_url += '&include_cards=1'
            twitter_list_url += '&include_ext_alt_text=true'
            twitter_list_url += '&include_quote_count=true'
            twitter_list_url += '&include_reply_count=1'
            twitter_list_url += '&tweet_mode=extended'
            twitter_list_url += '&include_entities=true'
            twitter_list_url += '&include_user_entities=true'
            twitter_list_url += '&include_ext_media_color=true'
            twitter_list_url += '&include_ext_media_availability=true'
            twitter_list_url += '&send_error_codes=true'
            twitter_list_url += '&simple_quoted_tweet=true'
            twitter_list_url += '&include_tweet_replies=false'
            twitter_list_url += '&count=' + str(count)
            twitter_list_url += '' if len(next_cursor) <= 0 else '&cursor=' + next_cursor
            twitter_list_url += '&userId=' + user_id
            twitter_list_url += '&ext=mediaStats%2ChighlightedLabel'
            twitter_list_response = req.get(twitter_list_url)

            twitter_list_json = json.loads(twitter_list_response.text)
            if "errors" in twitter_list_json:
                self.error = twitter_list_json.get("errors")[0]
                print("\t[+] code = " + str(twitter_list_json.get("errors")[0].get("code")) + ", message = " +
                      twitter_list_json.get("errors")[0].get("message"))
                break

            """
            # Use Cursor parameter to fetch data set
            use cursor to get the paging data is limited. (may be login firstly)
            can get the smaller data set than using count parameter.
            may fetch only 160 rows only.
            """
            # cursor_top = cursor_bottom = ""
            # for entry in twitter_list_json.get("timeline").get("instructions")[0].get("addEntries").get("entries"):
            #     if entry.get("content").get("operation") is None:
            #         continue
            #     cursor = entry.get("content").get("operation").get("cursor")
            #     if cursor.get("cursorType").lower() == "Top".lower():
            #         cursor_top = cursor.get("value")
            #     else:
            #         if cursor.get("cursorType").lower() == "Bottom".lower():
            #             cursor_bottom = cursor.get("value")
            # next_cursor = cursor_bottom
            # print("cursor_top = " + cursor_top + "; cursor_bottom = " + cursor_bottom + "; next_cursor = " + next_cursor)

            tweets_list = twitter_list_json.get("globalObjects").get("tweets")
            user = twitter_list_json.get("globalObjects").get('users')
            """
            # Use Count parameter to fetch data set
            can get a bigger data set than using Cursor parameter without login.
            """
            if count <= len(tweets_list):
                count_inc += 20
                count += count_inc
            else:
                count = 0
        return user, tweets_list

    def get_sort_value(self, media):
        str_p = media.get('created_at')
        # 'Wed Oct 07 16:59:07 +0000 2020' <==> '%a %b %d %H:%M:%S %z %Y'
        dateTime_p = datetime.datetime.strptime(str_p, '%a %b %d %H:%M:%S %z %Y')
        return dateTime_p

    def filter_tweets_video(self, tweets):

        result_list = []
        for name in tweets:
            media_list = None
            media_url = None
            try:
                media_url = tweets[name].get("entities")
                if media_url is not None: media_url = media_url.get("media")
                if media_url is not None: media_url = media_url[0]
                if media_url is not None: media_url = media_url.get("media_url")
            except ValueError:
                print('Error: ' + ValueError)
            if tweets[name].get("extended_entities") is not None:
                media_list = tweets[name].get("extended_entities").get("media")
            result_list.append({
                "tweet_id": tweets[name].get("id_str"),
                "full_text": tweets[name].get("full_text"),
                "user_id": tweets[name].get("user_id_str"),
                "created_at": tweets[name].get("created_at"),
                # media_type = video, photo
                "media_url": media_url if media_url is not None else "",
                "media_type": media_list[0].get("type") if media_list is not None else "",
                "tweet_url": media_list[0].get("expanded_url") if media_list is not None else ""
            })

        video_list = []
        for tweet in result_list:
            if tweet.get("media_type") == 'video':
                video_list.append(tweet)
                self.save_picture(tweet.get("media_url"))
        video_list.sort(key=self.get_sort_value, reverse=True)
        print("\t[+] twitter count = " + str(len(tweets)) + ", including video count = " + str(len(video_list)))
        return video_list


if __name__ == '__main__':
    tweet_url = "https://twitter.com/TwitterDev"
    output = 'D:/output'
    mediaViewer = TwitterMediaViewer(user_home_url=tweet_url, output_dir=output)
    tweets = mediaViewer.get_tweets_from_twitter()
    video_list = mediaViewer.filter_tweets_video(tweets)

    video_links = []
    for video in video_list:
        twitter_url = video["tweet_url"]
        video_links.append(twitter_url)
