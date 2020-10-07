#!/usr/bin/env python

import requests
import re
import json
import argparse
from twitter_dl import TwitterDownloader
from file_lines_access import FileLinesAccess

class TwitterMediaViewer:

    def __init__(self, user_home_url):
        self.requests = requests.Session()
        self.user_home_url = user_home_url
        self.screen_name = user_home_url.split('/')[3].lower()
        print("[+] user_home_url = " + user_home_url + ", screen_name = " + self.screen_name)

    def get_video_list(self):
        main_js_file_response = self.__get_main_js()
        self.__get_bearer_token(main_js_file_response)
        self.__get_activate_token()
        self.__get_user_id(main_js_file_response)
        if self.user_id == '-1':
            return []
        media_list = self.__get_media_list()
        video_list = self.__get_video_list(media_list)
        print("\t[+] twitter count = " + str(len(media_list)) + ", including video count = " + str(len(video_list)))
        return video_list

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
        req.headers.update({"Authorization": authorization})
        # print("authorization:" + authorization)


    def __get_activate_token(self):
        req = self.requests
        res = req.post("https://api.twitter.com/1.1/guest/activate.json")
        # print("activate:" + res.text)
        res_json = json.loads(res.text)
        req.headers.update({'x-guest-token': res_json.get('guest_token')})

    def __get_user_id(self, main_js_file_response):
        req = self.requests
        screen_name = self.screen_name

        variables_dict = '{"screen_name":"' + screen_name + '","withHighlightedLabel":true}'
        variables_str = 'variables=' + str(variables_dict).replace(' ', '').replace('{', '%7B').replace('\"', '%22').replace(':', '%3A').replace(',', '%2C').replace('}', '%7D')
        # print("UserByScreenName Param:" + variables_str)
        user_by_screen_name_prefix_pattern = '\\{queryId:\\"[a-zA-Z]+-_[a-zA-Z0-9]+\\",operationName:\\"UserByScreenName\\",operationType:\\"query\\"\\}'
        user_by_screen_name_prefix = re.findall(user_by_screen_name_prefix_pattern, main_js_file_response)[0]
        user_by_screen_name_prefix = str(user_by_screen_name_prefix).replace("queryId", "\"queryId\"").replace("operationName", "\"operationName\"").replace("operationType", "\"operationType\"")
        # print("user_by_screen_name_prefix:" + user_by_screen_name_prefix)
        user_by_screen_name_prefix_json = json.loads(user_by_screen_name_prefix)
        user_by_screen_name_url = "https://api.twitter.com/graphql/" + user_by_screen_name_prefix_json.get("queryId") + "/UserByScreenName?" + variables_str
        # print("UserByScreenName URL:" + user_by_screen_name_url)
        req.headers.update({"content-type": "application/json"})
        user_by_screen_name_response = req.get(user_by_screen_name_url)
        # print(user_by_screen_name_response.text)
        user_by_screen_name_json = json.loads(user_by_screen_name_response.text)
        if 'errors' not in user_by_screen_name_json:
            user_id = user_by_screen_name_json.get("data").get("user").get("rest_id")
            print("\t[+] user_id = "+user_id)
            self.user_id = user_id
        else:
            self.user_id = '-1'
            self.error = user_by_screen_name_json.get("errors")[0]
            print("\t[+]" + "code = " + str(user_by_screen_name_json.get("errors")[0].get("code")) + ", message = " + user_by_screen_name_json.get("errors")[0].get("message"))


    def __get_media_list(self):
        req = self.requests
        user_id = self.user_id

        count = 20
        count_inc = 20
        result_tweets = []
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
                print("\t[+] code = " + str(twitter_list_json.get("errors")[0].get("code")) + ", message = " + twitter_list_json.get("errors")[0].get("message"))
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
            result_tweets.clear()
            for name in tweets_list:
                media_list = None
                if tweets_list[name].get("extended_entities") is not None:
                    media_list = tweets_list[name].get("extended_entities").get("media")
                result_tweets.append({
                    "tweet_id": tweets_list[name].get("id_str"),
                    "full_text": tweets_list[name].get("full_text"),
                    "user_id": tweets_list[name].get("user_id_str"),
                    "created_at": tweets_list[name].get("created_at"),
                    # media_type = video, photo
                    "media_type": media_list[0].get("type") if media_list is not None else "",
                    "tweet_url": media_list[0].get("expanded_url") if media_list is not None else ""
                })
            # print("fetching tweet count = " + str(len(result_tweets)))
            """
            # Use Count parameter to fetch data set
            can get a bigger data set than using Cursor parameter without login.
            """
            if count <= len(result_tweets):
                count_inc += 20
                count += count_inc
            else:
                count = 0
        return result_tweets


    def __get_video_list(self, media_list):
        video_list = []
        for tweet in media_list:
            if tweet.get("media_type") == 'video':
                video_list.append(tweet)

        return video_list


if __name__ == '__main__':
    import sys

    if sys.version_info[0] == 2:
        print('Python3 is required.')
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('tweet_url', help='The user home URL on Twitter (https://twitter.com/<screen_name>).')
    parser.add_argument('-l', '--link_file', dest='link_file', default='./video-links.txt', help='The file to store the twitter links.')
    args = parser.parse_args()

    mediaViewer = TwitterMediaViewer(args.tweet_url)
    video_list = mediaViewer.get_video_list()
    video_links = []
    for video in video_list:
        twitter_url = video["tweet_url"]
        video_links.append(twitter_url)

    if len(video_links) > 0:
        file_lines_access = FileLinesAccess(args.link_file)
        file_lines_access.saveLines(video_links)

