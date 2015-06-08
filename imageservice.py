#!/usr/bin/env python

import time
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler 
import logging
import iris
import subprocessing as sp

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


def run_async(func):
    """
        run_async(func)
            function decorator, intended to make "func" run in a separate
            thread (asynchronously).
            Returns the created Thread object

            E.g.:
            @run_async
            def task1():
                do_something

            @run_async
            def task2():
                do_something_too

            t1 = task1()
            t2 = task2()
            ...
            t1.join()
            t2.join()
    """
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target = func, args = args, kwargs = kwargs)
        func_hl.start()
        return func_hl

    return async_func


class MyHandler(PatternMatchingEventHandler):
    patterns = ["*.pp"]

    def process(self, event):
        try:
            @async_func
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