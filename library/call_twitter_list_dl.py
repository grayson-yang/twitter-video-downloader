
if __name__ == '__main__':
    import sys

    if sys.version_info[0] == 2:
        print('Python3 is required.')
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('tweet_url', help='The user home URL on Twitter (https://twitter.com/<screen_name>).')
    parser.add_argument('-l', '--link_file', dest='link_file', default='./video-links.txt', help='The file to store the twitter links.')
    args = parser.parse_args()

    mediaViewer = TwitterMediaViewer(args.tweet_url, 'D:/output')
    tweets = mediaViewer.get_tweets_from_twitter()
    video_list = mediaViewer.filter_tweets_video(tweets)

    video_links = []
    for video in video_list:
        twitter_url = video["tweet_url"]
        video_links.append(twitter_url)

    # if len(video_links) > 0:
    #     file_lines_access = FileLinesAccess(args.link_file)
    #     file_lines_access.saveLines(video_links)

    tweets = mediaViewer.get_tweets_from_disk()
    if tweets is None:
        video_list = mediaViewer.filter_tweets_video(tweets)