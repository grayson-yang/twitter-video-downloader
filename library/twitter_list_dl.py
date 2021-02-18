#!/usr/bin/env python
import datetime
import os
from pathlib import Path

import requests
import re
import json
import argparse
import urllib.parse

from library.DownloadResourceByTweet import DownloadResourceByTweet

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
        self.main_js = {}
        print("[+] user_home_url = " + user_home_url + ", screen_name = " + self.screen_name)

    def get_tweets_from_twitter(self):
        main_js_file_response = self.__get_main_js()
        self.__get_bearer_token(main_js_file_response)
        self.__get_activate_token()
        self.__get_user_id()
        if self.user_id == '-1':
            return {}
        self.__get_following_list()
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

    def __save_data(self, file, content):
        with open(file, 'w') as f:
            f.writelines(content)

    def __analyze_main_js(self, main_js_content):
        # UserByScreenName, Following, Followers
        # Query Id for Screen Name
        regular_pattern = '\\{queryId:\\"[a-zA-Z0-9_-]+\\",operationName:\\"UserByScreenName\\",operationType:\\"query\\"\\}'
        regular_match_list = re.findall(regular_pattern, main_js_content)
        if len(regular_match_list) <= 0:
            print('[+] Error: could not find queryId for Screen Name.')
        else:
            match_item = regular_match_list[0]
            match_item = str(match_item).replace("queryId", "\"queryId\"").replace(
                "operationName", "\"operationName\"").replace("operationType", "\"operationType\"")
            print("[+] Find Screen Name JSON : " + match_item)
            temp_json = json.loads(match_item)
            queryId = temp_json.get("queryId")
            self.main_js["screen_name.queryId"] = queryId

        # Query Id for Following
        regular_pattern = '\\{queryId:\\"[a-zA-Z0-9_-]+\\",operationName:\\"Following\\",operationType:\\"query\\"\\}'
        regular_match_list = re.findall(regular_pattern, main_js_content)
        if len(regular_match_list) <= 0:
            print('[+] Error: could not find queryId for Following.')
        else:
            match_item = regular_match_list[0]
            match_item = str(match_item).replace("queryId", "\"queryId\"").replace(
                "operationName", "\"operationName\"").replace("operationType", "\"operationType\"")
            print("[+] Find Following JSON : " + match_item)
            temp_json = json.loads(match_item)
            queryId = temp_json.get("queryId")
            self.main_js["following.queryId"] = queryId

        return True

    def __get_main_js(self):
        req = self.requests
        user_home_url = self.user_home_url

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
        req.headers.update({"User-Agent": user_agent})
        user_home_response = req.get(user_home_url).text

        main_js_pattern = 'https://abs.twimg.com/responsive-web/client-web/main.*.js'
        main_js_file_url = re.findall(main_js_pattern, user_home_response)[0]
        main_js_file_response = req.get(main_js_file_url).text

        self.__analyze_main_js(main_js_content=main_js_file_response)

        return main_js_file_response

    def __get_bearer_token(self, main_js_file_response):
        req = self.requests

        authorization_pattern = '[A-Za-z0-9]+%3D[A-Za-z0-9]+'
        authorization = "Bearer " + re.findall(authorization_pattern, main_js_file_response)[0]
        print('[+] Authorization is : ' + authorization)
        req.headers.update({"Authorization": authorization})
        self.authorization = authorization

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

    def __parse_request_variables(self, variables):
        parseMap = {' ': '', '{': '%7B', '\"': '%22', ':': '%3A', ',': '%2C', '}': '%7D'}
        for key in parseMap:
            variables = str(variables).replace(key, parseMap[key])
        return variables

    def __get_user_id(self):
        req = self.requests
        screen_name = self.screen_name

        variables_dict = '{"screen_name":"' + screen_name + '","withHighlightedLabel":true}'
        variables_str = 'variables=' + self.__parse_request_variables(variables_dict)
        print("[+] UserByScreenName Param:" + variables_str)

        host = 'https://twitter.com'
        path = "/i/api/graphql/" + self.main_js.get("screen_name.queryId") + "/UserByScreenName?" + variables_str
        user_by_screen_name_url = host + path
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

    def __get_following_list(self):
        req = self.requests
        user_id = self.user_id
        variables_json = {
            "userId": user_id,
            "count": 20,
            "withHighlightedLabel": False,
            "withTweetQuoteCount": False,
            "includePromotedContent": False,
            "withTweetResult": False,
            "withUserResult": True
        }
        variables = json.dumps(variables_json)
        print('\t[+] variables : ' + variables)
        variables = self.__parse_request_variables(variables)
        host = "https://twitter.com"
        queryPath = "/i/api/graphql/" + self.main_js["following.queryId"] + "/Following?variables=" + variables
        requestUrl = host + queryPath
        print('\t[+] Following List : ' + requestUrl)
        print('\t[+] Authorization is : ' + req.headers["Authorization"])

        # req.headers.update({"x-csrf-token": "99207d169ca26a7c5ecee8e8a94c16fb651aadd4ed9a3f6525d972bcfcd453d238497a7e866e7e6edda318f48d26c26aa120c23fa559d66bc19fbb7dc75e0f31ef981465e893f2106d8d5d5d00ee1bae"})
        # req.headers.update({"x-twitter-active-user": "yes", "x-twitter-auth-type": "OAuth2Session", "x-twitter-client-language": "zh-cn"})

        following_api_response = req.get(requestUrl)
        print(following_api_response.text)

    def __submit_all(self):
        variableMap = {'include_profile_interstitial_type': 1,
                       'include_blocking': 1,
                       'include_blocked_by': 1,
                       'include_followed_by': 1,
                       'include_want_retweets': 1,
                       'include_mute_edge': 1,
                       'include_can_dm': 1,
                       'include_can_media_tag': 1,
                       'skip_status': 1,
                       'cards_platform': 'Web-12',
                       'include_cards': 1,
                       'include_ext_alt_text': True,
                       'include_quote_count': True,
                       'include_reply_count': 1,
                       'tweet_mode': 'extended',
                       'include_entities': True,
                       'include_user_entities': True,
                       'include_ext_media_color': True,
                       'include_ext_media_availability': True,
                       'send_error_codes': True,
                       'simple_quoted_tweet': True,
                       'count': 20,
                       'ext': 'mediaStats,highlightedLabel'
                       }


if __name__ == '__main__':
    tweet_url = "https://twitter.com/TwitterDev"
    screen_name = "TwitterDev"
    output = 'D:/output'
    mediaViewer = TwitterMediaViewer(user_home_url=tweet_url, output_dir=output)
    # fetch & update Tweet List from Twitter Server.
    tweets = mediaViewer.get_tweets_from_twitter()
