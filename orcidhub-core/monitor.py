import logging
import os
import signal
import threading

import inotify.adapters


def _monitor(path):

    i = inotify.adapters.InotifyTree(bytes(path, encoding="utf-8"))

    while True:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                if 'IN_CLOSE_WRITE' in type_names and filename.endswith(b".py"):
                    logging.info(
                        "monitor (pid=%d): %s/%s changed, restarting!",
                        os.getpid(), path, filename)
                    os.kill(os.getpid(), signal.SIGKILL)

def start(path):

    logging.basicConfig(level=logging.INFO)
    logging.info("** monitoring: %s", path)
    t = threading.Thread(target=_monitor, args=(path,))
    t.setDaemon(True)
    t.start()

    logging.info('Started change monitor. (pid=%d)', os.getpid())
