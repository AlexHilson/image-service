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
        patterns = config.source_files

        def process(self, event):
            try:
                sp.call(["./imageproc.py", "--analysis", call_args.analysis, event.src_path])
            except Exception as e:
                raise
            else:
                logger.info("Finished processing " + event.src_path)

        def on_created(self, event):
            logger.info("------------------------------------")
            logger.info(event.src_path + " " + event.event_type)
            logger.info("Processing " + event.src_path)
            success = False
            for attempt in range(100):
                time.sleep(2)
                try:
                    self.process(event)
                except KeyboardInterrupt:
                    raise
                except BaseException as e:
                    pass
                else:
                    success = True
                    break
            if not success:
                logger.exception(e)

    
    argparser = ap.ArgumentParser()
    argparser.add_argument("-a", "--analysis", default="default",
        type=str, help="Name of analysis settings, as defined in config.py")
    call_args = argparser.parse_args()

    observer = Observer()
    observer.schedule(MyHandler(), path=config.thredds_server)
    observer.start()

    logger.info("******* Image Service started *******")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("******* Image Service stopped *******")
        observer.stop()
    observer.join()

