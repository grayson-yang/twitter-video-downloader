"""
TwitterInstanceData.py
Collection for twitter resource.
"""
import argparse
import threading
import time

from flask import json

from collection.ScheduleTimer import ScheduleTimer


class TwitterInstanceData(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        scheduleTimer = ScheduleTimer()
        scheduleTimer.start()
        self.timer = scheduleTimer

    def get_white_list(self):
        with open('../document/white_list.json', 'r') as f:
            f.seek(0, 0)
            lines = f.readlines()
        content = ''
        for line in lines:
            content += line

        white_list = json.loads(content)
        return white_list

    def run(self):
        localtime = time.asctime(time.localtime(time.time()))
        print(localtime + ' - Thread [' + self.get_name() + '] running.')
        white_list = self.get_white_list()
        for key in white_list:
            task = {
                "type": "twitter",
                "screen_name": key
            }
            self.timer.addTask(task)

    def get_name(self):
        return 'TwitterInstanceData'

if __name__ == '__main__':
    import sys

    if sys.version_info[0] == 2:
        print('Python3 is required.')
        sys.exit(1)

    parser = argparse.ArgumentParser()
    # parser.add_argument('tweet_url', help='The user home URL on Twitter (https://twitter.com/<screen_name>).')
    # parser.add_argument('-l', '--link_file', dest='link_file', default='./video-links.txt', help='The file to store the twitter links.')
    # args = parser.parse_args()

    twitterInstanceData = TwitterInstanceData()
    twitterInstanceData.start()
