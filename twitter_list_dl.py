#!/usr/bin/env python

import requests
import re
import json
import argparse
from twitter_dl import TwitterDownloader

class TwitterMediaViewer:

    def __init__(self, user_home_url):
        self.requests = requests.Session()
        self.user_home_url = user_home_url
        self.screen_name = user_home_url.split('/')[3].lower()

    def get_video_list(self):
        main_js_file_response = self.__get_main_js()
        self.__get_bearer_token(main_js_file_response)
        self.__get_activate_token()
        self.__get_user_id(main_js_file_response)
        media_list = self.__get_media_list()
        return self.__get_video_list(media_list)

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
        print("authorization:" + authorization)


    def __get_activate_token(self):
        req = self.requests
        res = req.post("https://api.twitter.com/1.1/guest/activate.json")
        print("activate:" + res.text)
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
        user_id = user_by_screen_name_json.get("data").get("user").get("rest_id")
        print("user_id="+user_id)
        self.user_id = user_id


    def __get_media_list(self):
        req = self.requests
        user_id = self.user_id

        count = 20
        result_tweets = []
        twitter_home_url = 'https://api.twitter.com/2/timeline/profile/'
        twitter_media_url = 'https://api.twitter.com/2/timeline/media/'

        while count > 0:
            twitter_list_url = twitter_media_url
            twitter_list_url +=  user_id + '.json'
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
            # twitter_list_url += '&cursor=' + cursor
            twitter_list_url += '&userId=' + user_id
            twitter_list_url += '&ext=mediaStats%2ChighlightedLabel'
            twitter_list_response = req.get(twitter_list_url)

            twitter_list_json = json.loads(twitter_list_response.text)
            tweets_list = twitter_list_json.get("globalObjects").get("tweets");
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
            print("fetching tweet count = " + str(len(result_tweets)))
            if count <= len(result_tweets):
                count += 20
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
    parser.add_argument('tweet_url', help = 'The user home URL on Twitter (https://twitter.com/<screen_name>).')
    parser.add_argument('-o', '--output', dest='output', default = './output', help = 'The directory to output to. The structure will be: <output>/video/.')
    parser.add_argument('-d', '--debug', default=0, action='count', dest='debug', help = 'Debug. Add more to print out response bodies (maximum 2).')
    parser.add_argument('-r', '--resolution', dest='resolution', default=0, help='The resolution of video. 0 = All, 1 = Low (320*180), 2 Medium (640*360), 3 High (1280*720).')
    args = parser.parse_args()

    mediaViewer = TwitterMediaViewer(args.tweet_url)
    video_list = mediaViewer.get_video_list()
    for video in video_list:
        tweet_url = video["tweet_url"]
        twitter_dl = TwitterDownloader(tweet_url, args.output, int(args.resolution), args.debug)
        twitter_dl.download()

