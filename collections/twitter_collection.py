"""
twitter_collection.py
Collection for twitter resource.
"""
import argparse
import queue
import threading
import time

from flask import json


class AbstractCollection(threading.Thread):
    next_time = 0
    def __init__(self, timer):
        threading.Thread.__init__(self)
        self.timer = timer

    def get_name(self):
        return ""

    def get_delay(self):
        return 10

    def get_next_time(self):
        return self.next_time

    def set_next_time(self, value):
        self.next_time = value


class WhiteListCollection(AbstractCollection):

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
        print(localtime + ' - Collection [' + self.get_name() + '] collecting data.')
        white_list = self.get_white_list()
        for key in white_list:
            task = {
                "type": "twitter",
                "screen_name": key
            }
            self.timer.addTask(task)

    def get_name(self):
        return 'WhiteList_Collection'

    def get_delay(self):
        return 10


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
        # TODO: execute Twitter API.
        self.after_run()

    def after_run(self):
        task = {
            "type": "twitter",
            "screen_name": self.screen_name
        }
        self.timer.addTask(task, self.get_delay())

    def get_name(self):
        return self.screen_name + '_Collection'


class ScheduleTimer(threading.Thread):

    """ use query rather than array(stack) to avoid the bottom task never execute. """
    tasks = queue.Queue()
    scheduled = queue.Queue()

    def __init__(self):
        threading.Thread.__init__(self)


    def addTask(self, collection, delay=0):
        # right now or not.
        collection["next_time"] = time.time() + delay
        self.tasks.put(collection)


    def run(self):
        while True:
            self.__schedule_timer()
            self.__task_timer()
            time.sleep(0.01)


    def __schedule_timer(self):
        if self.scheduled.empty():
            return
        task = self.scheduled.get()
        if task is None:
            return
        print(json.dumps(task))
        try:
            twitterDownload = TwitterCollection(self, task["screen_name"])
            twitterDownload.start()
        except ValueError:
            localtime = time.asctime(time.localtime(time.time()))
            print(localtime + ' Collection ' + task["screen_name"] + ' run errors!')


    def __task_timer(self):
        if self.tasks.empty():
            return
        task = self.tasks.get()
        if task is None:
            return
        if task["next_time"] <= time.time():
            self.scheduled.put(task)
        else:
            self.tasks.put(task)


if __name__ == '__main__':
    import sys

    if sys.version_info[0] == 2:
        print('Python3 is required.')
        sys.exit(1)

    # parser = argparse.ArgumentParser()
    # parser.add_argument('tweet_url', help='The user home URL on Twitter (https://twitter.com/<screen_name>).')
    # parser.add_argument('-l', '--link_file', dest='link_file', default='./video-links.txt', help='The file to store the twitter links.')
    # args = parser.parse_args()

    scheduleTimer = ScheduleTimer()
    scheduleTimer.start()
    whiteListCollection = WhiteListCollection(scheduleTimer)
    whiteListCollection.start()