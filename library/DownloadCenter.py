#!/usr/bin/env python
import os
import threading

from library.AppData import AppData
from library.DownloadResourceByTweet import DownloadResourceByTweet
from library.twitter_dl import TwitterDownloader
from library.twitter_list_dl import TwitterMediaViewer
import argparse

# SettingsEntry Initiation
settings_entry = AppData.getInstance().getSettingsEntry()
setting_path = os.path.abspath('./config/settings.json')
settings_entry.setSettingsPath(setting_path)
settings_entry.loadSettings()

is_multiThread = True

def download(screen_name, debug=0):
    # load Settings
    settings_entry.loadSettings()
    output = settings_entry.getRootStorage()
    networkStatus = settings_entry.getNetworkStatus()

    if networkStatus is False:
        tweet_url = "https://twitter.com/" + screen_name
        # Step-1, fetch & update Tweet List from Twitter Server into Local Disk.
        mediaViewer = TwitterMediaViewer(user_home_url=tweet_url, output_dir=output)
        tweets = mediaViewer.get_tweets_from_twitter()

    # Step-2, get Tweets from Local Disk.
    downloader = DownloadResourceByTweet(screen_name=screen_name, output_dir=output)
    # load the Tweets from Disk
    tweets = downloader.get_tweets_from_disk()

    # Step-3, operate for the Tweets: find the video in Tweets.
    # download the picture of Video
    downloader.download_tweets_video_picture(tweets)
    # filter video in Tweets
    video_tweets = downloader.filter_tweets_video(tweets)
    video_links = []
    for video in video_tweets:
        twitter_url = video["tweet_url"]
        video_links.append(twitter_url)

    # Step-4, save the video of Tweet
    threadArray = []
    for tweet_url in video_links:
        # load Settings
        settings_entry.loadSettings()
        output = settings_entry.getRootStorage()
        resolution = settings_entry.getResolution()
        save_as_mp4 = settings_entry.getMp4()
        download_duration = settings_entry.getDuration()
        if is_multiThread is False:
            twitter_dl = TwitterDownloader(tweet_url=tweet_url, output_dir=output, resolution=resolution, debug=debug,
                                           save_as_mp4=save_as_mp4)
            twitter_dl.download(download_duration=download_duration)
        else:
            thread = DownloadTweetThread(tweet_url=tweet_url, output_dir=output, resolution=resolution, debug=debug,
                                         save_as_mp4=save_as_mp4, download_duration=download_duration)
            thread.start()
            threadArray.append(thread)

    for thread in threadArray:
        thread.join()


class DownloadTweetThread(threading.Thread):
    def __init__(self, tweet_url, output_dir='./output', resolution=0, debug=0, save_as_mp4=True, download_duration=10):
        self.tweet_url = tweet_url
        self.output_dir = output_dir
        self.debug = debug
        self.save_as_mp4 = save_as_mp4
        if resolution < 0:
            resolution = 0
        self.resolution = resolution
        self.download_duration = download_duration
        if debug > 2:
            self.debug = 2

    def run(self):
        twitter_dl = TwitterDownloader(tweet_url=self.tweet_url, output_dir=self.output, resolution=self.resolution,
                                       debug=self.debug,
                                       save_as_mp4=self.save_as_mp4)
        twitter_dl.download(download_duration=self.download_duration)


class DownloadThread(threading.Thread):
    def __init__(self, screen_name, debug):
        threading.Thread.__init__(self)
        self.screen_name = screen_name
        self.debug = debug

    def run(self):
        download(screen_name=self.screen_name, debug=self.debug)


if __name__ == '__main__':

    import sys

    if sys.version_info[0] == 2:
        print('Python3 is required.')
        sys.exit(1)

    # Parameters: -o D:/output -r 3 -d 0 -n TwitterDev
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--screen_name', help='The Screen Name on Twitter (https://twitter.com/<screen_name>).')
    parser.add_argument('-o', '--output', dest='output', default='./output',
                        help='The directory to output to. The structure will be: <output>/video/.')
    parser.add_argument('-d', '--debug', default='0', dest='debug',
                        help='Debug. Add more to print out response bodies (maximum 2).')
    parser.add_argument('-r', '--resolution', dest='resolution', default=0,
                        help='The resolution of video. 0 = All, 1 = Low (320*180), 2 Medium (640*360), 3 High (1280*720).')
    parser.add_argument("-s", '--sleep', dest='sleep', default=10,
                        help='The milliseconds while downloading ts files. Default is 10 milliseconds.')
    args = parser.parse_args()

    tweet_url = "https://twitter.com/" + args.screen_name
    screen_name = args.screen_name
    output = args.output
    # 0 All, 1 Low, 2 Medium, 3 High
    resolution = int(args.resolution)
    debug = int(args.debug)
    download_duration = int(args.sleep)
    save_as_mp4 = True
    network_status = False

    # Save Settings
    settings_entry.setDuration(download_duration)
    settings_entry.setResolution(resolution)
    settings_entry.setMp4(save_as_mp4)
    settings_entry.setRootStorage(output)
    settings_entry.setNetworkStatus(network_status)
    settings_entry.saveSettings()

    threadArray = []
    sceen_name_list = screen_name.split(',')
    for screen_name in sceen_name_list:
        screen_name = screen_name.strip(' ')
        if len(screen_name) > 0:
            if is_multiThread is False:
                try:
                    download(screen_name=screen_name, debug=debug)
                except:
                    print("Interrupt of " + screen_name)
            else:
                thread = DownloadThread(screen_name, debug)
                thread.start()
                threadArray.append(thread)

    for thread in threadArray:
        thread.join()
