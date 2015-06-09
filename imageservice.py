#!/usr/bin/env python

import argparse as ap
import time
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler 
import logging
import iris
import subprocess as sp

import sys
sys.path.append(".")
import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler('imageservice.log', maxBytes=1e6, backupCount=3)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


if __name__ == '__main__':
    """
    Watchdog class defined in __main__ so that it has access to the
    config variables

    """
    class MyHandler(PatternMatchingEventHandler):
        @staticmethod
        def process(data_file):
            try:
                sp.call(["./imageproc.py", "--analysis", call_args.analysis, data_file])
            except Exception as e:
                raise
            else:
                logger.info("Finished processing " + data_file)

        def on_moved(self, event):
            logger.info("------------------------------------")
            logger.info(event.dest_path + " detected")
            time.sleep(5)
            try:
                logger.info("Processing " + event.dest_path)
                self.process(event.dest_path)
            except KeyboardInterrupt:
                raise
            except BaseException as e:
                logger.exception(e)

    
    argparser = ap.ArgumentParser()
    argparser.add_argument("-a", "--analysis", default="default",
        type=str, help="Name of analysis settings, as defined in config.py")
    call_args = argparser.parse_args()

    observer = Observer()
    observer.schedule(MyHandler(patterns=[config.source_files],
                                ignore_patterns=["*.pp~"]),
                      path=config.thredds_server)
    observer.start()

    logger.info("******* Image Service started *******")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("******* Image Service stopped *******")
        observer.stop()
    observer.join()

