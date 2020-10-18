import queue
import threading
import time

from collection.TwitterCollection import TwitterCollection


class ScheduleTimer(threading.Thread):
    """ use query rather than array(stack) to avoid the bottom task never execute. """
    tasks = queue.Queue()

    def __init__(self):
        threading.Thread.__init__(self)

    def addTask(self, collection, delay=0):
        # right now or not.
        collection["next_time"] = time.time() + delay
        self.tasks.put(collection)

    def run(self):
        while True:
            self.__task_timer()
            time.sleep(0.01)

    def __task_timer(self):
        if self.tasks.empty():
            return
        task = self.tasks.get()
        if task is None:
            return
        if task["next_time"] <= time.time():
            try:
                twitterDownload = TwitterCollection(self, task["screen_name"])
                twitterDownload.start()
            except ValueError:
                localtime = time.asctime(time.localtime(time.time()))
                print(localtime + ' Collection ' + task["screen_name"] + ' run errors!')
        else:
            self.tasks.put(task)