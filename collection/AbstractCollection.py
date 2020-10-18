import threading


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
