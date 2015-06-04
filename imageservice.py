#!/usr/bin/env python

import time
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler 
import logging
import iris

import sys
sys.path.append(".")
import imageproc

THREDDS_SERVER = "/Users/niall/Data/PretendTHREDDS/"
DATA_SERVER = "http://ec2-52-16-246-202.eu-west-1.compute.amazonaws.com:9000/molab-3dwx-ds/images/"
DATA_CONSTRAINT = iris.Constraint(model_level_number=lambda v: v.point < 60)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler('imageservice.log', maxBytes=1024, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class MyHandler(PatternMatchingEventHandler):
    patterns = ["*.pp"]

    def process(self, event):
        logger.info("Processing " + event.src_path)
        try:
	        imageproc.makeImage(DATA_CONSTRAINT,
	                            event.src_path,
	                            DATA_SERVER)
        except Exception as e:
	        raise
        logger.info("Finished processing " + event.src_path)

    def on_created(self, event):
    	logger.info(event.src_path + " " + event.event_type)
        self.process(event)

if __name__ == '__main__':
    observer = Observer()
    observer.schedule(MyHandler(), path=THREDDS_SERVER)
    observer.start()

    logger.info("Image Service started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Image Service stopped")
        observer.stop()

    observer.join()