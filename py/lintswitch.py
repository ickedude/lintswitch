""" lintswitch lints your code in the background.
http://github.com/grahamking/lintswitch
"""

import sys
import socket
import logging
import os
import os.path
from multiprocessing import Queue, Process

import checkers
import emitters
import http_server

LOG_FILE = '/tmp/lint_switch.log'
LOG = logging.getLogger(__name__)

WORK_DIR = os.path.join(os.path.expanduser('~'), '.lintswitch')


def main(argv=None):
    """Start here"""
    if not argv:
        argv = sys.argv

    logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)
    LOG.debug('lintswitch start')

    work_dir = WORK_DIR
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    queue = Queue()
    check_proc = Process(target=worker, args=(queue,work_dir))
    check_proc.start()

    server = Process(target=http_server.http_server, args=(work_dir,))
    server.start()

    # Listen for connections from vim (or other) plugin
    listener = socket.socket()
    listener.bind(('127.0.0.1', 4008))
    listener.listen(10)

    try:
        main_loop(listener, queue)
    except KeyboardInterrupt:
        listener.close()
        print('Bye')
        return 0


def main_loop(listener, queue):
    """Wait for connections and process them.
    @param listener a socket.socket, open and listening.
    """

    while True:
        conn, _ = listener.accept()
        data = conn.makefile().read()
        conn.close()

        queue.put(data)


def worker(queue, work_dir):
    """Takes filename from queue, checks them and displays (emit) result.
    """

    while 1:
        filename = queue.get()
        filename = filename.strip()
        LOG.info(filename)

        errors, warnings, summaries = checkers.check(filename)
        emitters.emit(filename, errors, warnings, summaries, work_dir)


if __name__ == '__main__':
    sys.exit(main())
