#!/usr/bin/env python
from library.DownloadResourceByTweet import DownloadResourceByTweet
from library.twitter_dl import TwitterDownloader
from library.twitter_list_dl import TwitterMediaViewer

if __name__ == '__main__':

    tweet_url = "https://twitter.com/TwitterDev"
    screen_name = "TwitterDev"
    output = 'D:/output'
    # 0 All, 1 Low, 2 Medium, 3 High
    resolution = 1
    debug = 0
    save_as_mp4 = True

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
        twitter_dl.download()