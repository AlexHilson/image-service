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
UK_V_EXTENT = [-13.62, 6.406, 47.924, 60.866]
REGRID_SHAPE = [400, 400, 35]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler('imageservice.log', maxBytes=1e6, backupCount=3)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class MyHandler(PatternMatchingEventHandler):
    patterns = ["*.pp"]

    def process(self, event):
        try:
	        imageproc.makeImage(DATA_CONSTRAINT,
	                            event.src_path,
	                            DATA_SERVER,
                                UK_V_EXTENT,
                                REGRID_SHAPE)
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
            except BaseException as e:
                pass
            else:
                success = True
                break
        if not success:
            logger.exception(e)

if __name__ == '__main__':
    observer = Observer()
    observer.schedule(MyHandler(), path=THREDDS_SERVER)
    observer.start()

    logger.info("******* Image Service started *******")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("******* Image Service stopped *******")
        observer.stop()

    observer.join()