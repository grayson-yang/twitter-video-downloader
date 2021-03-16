#!/usr/bin/env python
import datetime
import os
from pathlib import Path

import requests
import json
import urllib.parse
import time

class DownloadResourceByTweet:

    def __init__(self, screen_name, output_dir='./output'):
        self.requests = requests.Session()
        self.screen_name = str.lower(screen_name)
        self.output_dir = output_dir

    def check_picture(self, picture_url):
        print('\t[+] Checking Picture URL : ' + picture_url)
        picture_uri = urllib.parse.urlparse(picture_url).path
        exists = False
        if Path.exists(Path(self.output_dir) / picture_uri[1:]) is True:
            exists = True
        print('\t[+] ' + 'Exists [' + str(exists) + '], Picture URL : ' + picture_url)
        return exists

    """
    True if file exists or download successfully.
    """

    def save_picture(self, picture_url):
        # print('\t[+] Picture URL : ' + picture_url)
        try:
            picture_uri = urllib.parse.urlparse(picture_url).path

            if Path.exists(Path(self.output_dir) / picture_uri[1:]) is True:
                return True

            picture_response = self.requests.get(picture_url)
            Path.mkdir(Path(self.output_dir) / picture_uri[1:picture_uri.rindex('/')], parents=True, exist_ok=True)
            with open(Path(self.output_dir) / picture_uri[1:], 'wb') as f:
                f.write(picture_response.content)
                print('\t[+] Saved picture into ' + str(Path(self.output_dir) / picture_uri[1:]))
            return True
        except IOError:
            print("Error : " + IOError)
            return False

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

    def download_tweets_video_picture(self, tweets):

        result_list = []
        if tweets is None:
            return False
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
                picture_url = tweet.get("media_url")
                if self.check_picture(picture_url) is not True:
                    self.save_picture(tweet.get("media_url"))
                    time.sleep(1)
        video_list.sort(key=self.get_sort_value, reverse=True)
        print("\t[+] twitter count = " + str(len(tweets)) + ", including video count = " + str(len(video_list)))
        return True

    def filter_tweets_video(self, tweets):

        result_list = []
        if tweets is None:
            return result_list
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
        video_list.sort(key=self.get_sort_value, reverse=True)
        print("\t[+] twitter count = " + str(len(tweets)) + ", including video count = " + str(len(video_list)))
        return video_list


    def get_sort_value(self, media):
        str_p = media.get('created_at')
        # 'Wed Oct 07 16:59:07 +0000 2020' <==> '%a %b %d %H:%M:%S %z %Y'
        dateTime_p = datetime.datetime.strptime(str_p, '%a %b %d %H:%M:%S %z %Y')
        return dateTime_p


if __name__ == '__main__':
    screen_name = "TwitterDev"
    output = 'D:/output'
    downloader = DownloadResourceByTweet(screen_name=screen_name, output_dir=output)
    # Step-1, load the Tweets from Disk
    tweets = downloader.get_tweets_from_disk()
    # Step-2, operate for the Tweets.
    # example-1, download the picture of Video
    downloader.download_tweets_video_picture(tweets)
    # example-2, find video in tweets
    video_tweets = downloader.filter_tweets_video(tweets)

    video_links = []
    for video in video_tweets:
        twitter_url = video["tweet_url"]
        video_links.append(twitter_url)