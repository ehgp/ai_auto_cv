"""Linked In Jobs.

Selenium Job that will apply to jobs for you on LinkedIn.
For educational purposes only, not responsible for blocked accounts.
"""
import concurrent.futures
import datetime as dt
import logging
import logging.config
import os
import threading
from os import listdir
from os.path import isfile, join
from pathlib import Path

import nltk
import schedule
import yaml
from dotenv import load_dotenv

from jobboards.linkedin.linkedin import scrape_linkedin

# Paths
path = Path(os.getcwd())
load_dotenv()
# Logging
Path("log").mkdir(parents=True, exist_ok=True)
log_config = Path(path, "log_config.yaml")
timestamp = "{:%Y_%m_%d_%H_%M_%S}".format(dt.datetime.now())
with open(log_config, "r") as log_file:
    config_dict = yaml.safe_load(log_file.read())
    # Append date stamp to the file name
    log_filename = config_dict["handlers"]["file"]["filename"]
    base, extension = os.path.splitext(log_filename)
    base2 = "_" + os.path.splitext(os.path.basename(__file__))[0] + "_"
    log_filename = "{}{}{}{}".format(base, base2, timestamp, extension)
    config_dict["handlers"]["file"]["filename"] = log_filename
    logging.config.dictConfig(config_dict)
logger = logging.getLogger(__name__)


def run_job_boards():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        future = executor.submit(scrape_linkedin)
        futures.append(future)
        # Wait for all futures to complete
        concurrent.futures.wait(futures)


def main():
    """Main function."""
    logger.info("Starting Threading of Scrapers")
    # Run the requests inside a thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(run_job_boards)
    # logger.info("Ending main function")


if __name__ == "main":
    main()
