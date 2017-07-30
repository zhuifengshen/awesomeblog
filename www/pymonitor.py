#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-7-30
import sys
import os
import time
import subprocess
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

__author__ = 'Devin -- http://zhangchuzhao.site'


def log(s):
    print('[Monitor] %s' % s)


class MyFileSystemEventHandler(FileSystemEventHandler):
    def __init__(self, fn):
        super(MyFileSystemEventHandler, self).__init__()
        self.restart = fn

    def on_any_event(self, event):
        if event.src_path.endswith('.py'):
            log('Python source file changed: %s' % event.src_path)
            self.restart()

command = ['echo', 'ok']
process = None


def kill_process():
    global process
    if process:
        log('Kill process [%s]...' % process.pid)
        process.kill()
        process.wait()
        log('Process ended with code %s.' % process.returncode)
        process = None


def start_process():
    global process, command
    log('Start process %s...' % ' '.join(command))
    process = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)


def restart_process():
    kill_process()
    start_process()


def start_watch(path, callback):
    observer = Observer()
    observer.schedule(MyFileSystemEventHandler(restart_process), path, recursive=True)
    observer.start()
    log('Watching directory %s...' % path)
    start_process()
    try:
        while True:
            time.sleep(.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':
    # argv = sys.argv[1:]
    # if not argv:
    #     print('Usage: python3.6 pymonitor.py app.py')
    #     exit(0)
    # if argv[0] != 'python3.6':
    #     argv.insert(0, 'python3.6')
    # command = argv
    command = ['python3.6', 'app.py']
    path = os.path.abspath('.')
    start_watch(path, None)
