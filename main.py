from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
import os
import random
from time import sleep
from datetime import datetime
from datetime import timedelta 
import pytz
import logging
import requests

hour_start = 2
hour_end = 5
minute_start = 0
minute_end = 59
in_between_delay_minute = 5
scrapy_time = 30 # minute
next_check_hours = 20

TZ=pytz.timezone("Asia/Taipei")


logging.basicConfig(format='%(filename)s:%(levelname)s:%(message)s', level=logging.DEBUG)

TZ=pytz.timezone("Asia/Taipei")
magic_word = os.environ.get("MAGIC_WORD", None)
url_pattern = "https://%s.herokuapp.com"


def keepalive_job():
    hosts = os.environ.get("KA_HOSTS", None)
    for host in hosts.split():
        if host:
            response = requests.head(url_pattern % host, timeout=50)
            logging.debug("%s:%s:%s" % ("KA", host, response))


def midnight_job():
    hosts = os.environ.get("MN_HOSTS", None)
    for host in hosts.split():
        if host:
            response = requests.post(url_pattern % host, data=magic_word, timeout=50)
            logging.debug("%s:%s:%s" % ("KA", host, response))


def get_next_run_time(is_refresh_run):
    now = datetime.now(TZ)
    
    if( is_refresh_run ):
        next_run_time_ = now
    else:
        hour=random.randint(hour_start,hour_end)
        minute=random.randint(minute_start,minute_end)

        start_time = datetime(next_run_time.year,next_run_time.month,next_run_time.day,hour_start,minute_start,tzinfo=TZ)
        end_time = start_time.replace(hour=hour_end, minute=minute_end)
    
        logging.debug("next_run_time: %s" % next_run_time)
        logging.debug("start_time: %s" % start_time)
        logging.debug("end_time: %s" % end_time)
        if start_time <= now <= end_time:
            logging.debug("now in between")
            next_run_time_ = now + timedelta(minutes=in_between_delay_minute)
        elif now < start_time:
            logging.debug("now < start_time")
            next_run_time_ = next_run_time.replace(hour=hour,minute=minute)
        else:
            logging.debug("now > end_time")
            next_run_time_ = next_run_time + timedelta(days=1)
            next_run_time_ = next_run_time_.replace(hour=hour,minute=minute)

    return next_run_time_


next_run_time = get_next_run_time(True)

sched = BackgroundScheduler(timezone=TZ)
sched.start()

ka_job = sched.add_job(keepalive_job, trigger="interval", minutes=1)

while True:
    jobs=sched.get_jobs()
    
    ka_job_exist = False

    for job in jobs:
        if job.name == "midnight_job":
            ka_job_exist = True
            break

    if not ka_job_exist:
        next_run_time = get_next_run_time(False)
        mn_job = sched.add_job(midnight_job, next_run_time=next_run_time)
        logging.debug("new job scheduled at time: %s" % mn_job.next_run_time)
    
    time_diff = mn_job.next_run_time + timedelta(hours=next_check_hours) 
    sleep_seconds = next_check_hours * 60 * 60
    logging.debug("next check time: %s" % time_diff)
    sleep(sleep_seconds)
