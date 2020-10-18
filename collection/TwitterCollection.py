import time

from collection.AbstractCollection import AbstractCollection
from library.twitter_dl import TwitterDownloader
from library.twitter_list_dl import TwitterMediaViewer


class TwitterCollection(AbstractCollection):
    next_time = 0

    def __init__(self, timer, screen_name):
        AbstractCollection.__init__(self, timer)
        self.screen_name = screen_name
        self.setName(screen_name + '_collection')
        localtime = time.asctime(time.localtime(time.time()))
        print(localtime + ' - Collection [' + self.get_name() + '] starting.')

    def run(self):
        localtime = time.asctime(time.localtime(time.time()))
        print(localtime + ' - Collection [' + self.get_name() + '] collecting data.')
        # execute Twitter API.
        twitter_url = 'https://twitter.com/' + self.screen_name
        mediaViewer = TwitterMediaViewer(twitter_url, 'D:/output')
        tweets = mediaViewer.get_tweets_from_twitter()
        video_list = mediaViewer.filter_tweets_video(tweets)

        video_links = []
        for video in video_list:
            tweet_url = video["tweet_url"]
            video_links.append(tweet_url)

        output_dir = 'D:/output'
        resolution = 0
        debug = 1
        for tweet_url in video_links:
            try:
                twitter_dl = TwitterDownloader(tweet_url, output_dir, resolution, debug)
                twitter_dl.download()
            except ValueError:
                print('Error: ' + ValueError)
        self.after_run()

    def after_run(self):
        task = {
            "type": "twitter",
            "screen_name": self.screen_name
        }
        self.timer.addTask(task, self.get_delay())

    def get_name(self):
        return self.screen_name + '_Collection'

    def get_delay(self):
        return 60 * 60
