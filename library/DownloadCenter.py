#!/usr/bin/env python
from library.DownloadResourceByTweet import DownloadResourceByTweet
from library.twitter_dl import TwitterDownloader
from library.twitter_list_dl import TwitterMediaViewer
import argparse

def download(screen_name, output, resolution, debug=0, save_as_mp4=True, download_duration=10):
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
    for tweet_url in video_links:
        twitter_dl = TwitterDownloader(tweet_url=tweet_url, output_dir=output, resolution=resolution, debug=debug,
                                   save_as_mp4=save_as_mp4)
        twitter_dl.download(download_duration=download_duration)


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

    download(screen_name=screen_name, output=output, resolution=resolution, debug=debug, save_as_mp4=True, download_duration=download_duration)
