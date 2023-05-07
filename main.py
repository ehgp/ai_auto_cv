"""Linked In Jobs.

Selenium Job that will apply to jobs for you on LinkedIn.
For educational purposes only, not responsible for blocked accounts.
"""
import os
from pathlib import Path
import yaml
import logging
import logging.config
import datetime as dt
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import shutil
import time
import random
import pandas as pd
import string
import re
from nltk.corpus import stopwords
import sqlite3
from os import listdir
from os.path import isfile, join

import nltk

nltk.download("stopwords", quiet=True)

# Paths
path = Path(os.getcwd())
binary_path = Path(path, "chromedriver.exe")

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


def _remove_html_tags(text):
    """Remove html tags from a string."""
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def _save_html_to_file(response, title):
    """Save response to response.html."""
    with open(
        Path(path, f"{title}.html"),
        "w",
        encoding="utf-8",
    ) as fp:
        fp.write(response)


def _read_html(path: str) -> str:
    """Read HTML file to feed into BS."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def _load_config():
    """Load the configuration yaml and return dictionary of setttings.

    Returns:
        yaml as a dictionary.
    """
    config_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(config_path, "parameters.yaml")
    with open(config_path, "r") as config_file:
        config_defs = yaml.safe_load(config_file.read())

    if config_defs.values() is None:
        raise ValueError("parameters yaml file incomplete")

    return config_defs


class SeleniumLI:
    """Selenium LinkedIn.

    This will store a cookie session of your login and will initialize a driver.
    """

    def __init__(self) -> None:
        """Initialize."""
        logger.info("Configure ChromeOptions")
        self.options = Options()
        # self.options.page_load_strategy = "eager"
        # self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # self.options.add_experimental_option("useAutomationExtension", False)
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # self.options.add_experimental_option("prefs", prefs)
        # self.options.add_argument("user-data-dir=.profile-LI")
        # self.options.add_argument('--proxy-server=https://'+ self.proxies[0])
        # self.options.add_argument('--proxy-server=http://'+ self.proxies[0])
        # self.options.add_argument('--proxy-server=socks5://'+ self.proxies[0])
        # self.options.add_argument("--disable-notifications")
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_argument("--ignore-ssl-errors")
        # self.options.add_argument(
        #     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
        # )
        # self.options.add_argument('--headless')
        # self.options.add_argument('--window-size=1910x1080')
        # self.options.add_argument('--proxy-server=http://'+ proxies[0]))
        # self.options.add_argument("--disable-infobars")  # disabling infobars
        # self.options.add_argument("--disable-extensions")  # disabling extensions
        # self.options.add_argument("--disable-gpu")  # applicable to windows os only
        # self.options.add_argument("--no-sandbox")  # Bypass OS security model
        # self.options.add_argument(
        #     "--disable-dev-shm-usage"
        # )  # overcome limited resource problems
        # self.options.add_argument("--remote-debugging-port=9222")
        self.driver = webdriver.Chrome(
            executable_path=binary_path, options=self.options
        )

    def apply_ez(self):
        """Execute Easy Apply Automation."""
        logger.info("Log In")
        self.driver.get(cf["li_login"])
        time.sleep(random.randint(3, 5))
        self.driver.refresh()
        time.sleep(random.randint(3, 5))
        self.driver.refresh()
        time.sleep(random.uniform(0.15, 0.4))
        self.driver.find_element_by_id("username").send_keys(cf["linkedin_email"])
        time.sleep(random.uniform(0.15, 0.4))
        self.driver.find_element_by_id("password").send_keys(cf["linkedin_pwd"])
        time.sleep(random.uniform(0.15, 0.4))
        (
            WebDriverWait(self.driver, 10)
            .until(EC.element_to_be_clickable((By.XPATH, cf["xpath"]["login_btn"])))
            .click()
        )
        time.sleep(random.uniform(0.15, 0.4))
        # for i in range(0, 240, 24):
        for i in range(0, 24, 24):
            time.sleep(random.randint(3, 5))
            self.driver.get(
                cf["search_ezapp"].format(
                    keywords=cf["keywords"].replace(" ", "%20"),
                    location=cf["location"].replace(" ", "%20"),
                    page=i,
                )
            )
            time.sleep(random.randint(5, 10))
            content = self.driver.execute_script(
                "return document.getElementsByTagName('html')[0].innerHTML"
            )
            soup = BeautifulSoup(content, "lxml")
            _save_html_to_file(content, f"job_main_page_{i}")
            for link in soup.findAll(
                "li",
                class_=re.compile("jobs-search-results__list-item occludable-update*"),
            ):
                job_ids.append(link.get("data-occludable-job-id"))
            for job_id in job_ids:
                time.sleep(random.randint(3, 5))
                self.driver.get(cf["search_job"].format(job_id=job_id))
                time.sleep(random.randint(5, 10))
                content = self.driver.execute_script(
                    "return document.getElementsByTagName('html')[0].innerHTML"
                )
                soup = BeautifulSoup(content, "lxml")
                _save_html_to_file(content, f"job_id_{job_id}")

                try:
                    job_posts.append(
                        _remove_html_tags(
                            soup.find("button", class_=re.compile("jobs-save-button*"))
                            .text.replace("Save", "")
                            .replace("\n", " ")
                            .replace("  ", "")
                            .strip()
                        ).split(" at ")[0]
                    )
                except Exception as e:
                    print(e)
                    job_posts.append(None)
                print(job_posts)

                try:
                    job_employers.append(
                        _remove_html_tags(
                            soup.find("button", class_=re.compile("jobs-save-button*"))
                            .text.replace("Save", "")
                            .replace("\n", " ")
                            .replace("  ", "")
                            .strip()
                        ).split(" at ")[1]
                    )
                except Exception as e:
                    print(e)
                    job_employers.append(None)
                print(job_employers)

                try:
                    locations.append(
                        _remove_html_tags(
                            soup.find(
                                "span",
                                class_=re.compile("jobs-unified-top-card__bullet*"),
                            )
                            .text.replace("\n", " ")
                            .replace("  ", "")
                            .strip()
                        )
                    )
                except Exception as e:
                    print(e)
                    locations.append(None)
                print(locations)

                try:
                    job_descriptions.append(
                        " ".join(
                            [
                                word
                                for word in _remove_html_tags(
                                    soup.find(
                                        "div",
                                        class_=re.compile(
                                            "jobs-box__html-content jobs-description-content__text*"
                                        ),
                                    )
                                    .text.replace("\n", " ")
                                    .replace("  ", "")
                                    .split()
                                )
                                if word not in stopwords_dict
                            ]
                        )
                    )
                except Exception as e:
                    print(e)
                    job_descriptions.append(None)

                try:
                    job_salaries.append(
                        soup.find(
                            "div",
                            id_=re.compile("SALARY"),
                        )
                        .text.replace("\n", "")
                        .replace("  ", "")
                    )
                except Exception as e:
                    print(e)
                    job_salaries.append(None)
                print(job_salaries)

        self.driver.quit()


def main():
    """Scrape LinkedIn for jobs."""
    sli = SeleniumLI()
    sli.apply_ez()

    con = sqlite3.connect("jobs.db")
    cur = con.cursor()
    create_table = """CREATE TABLE IF NOT EXISTS jobs \
    (job_ids text, job_posts text,  job_employers text, \
    locations text, job_salaries text, job_descriptions text)"""
    logger.info("Creating Table jobs")
    cur.execute(create_table)
    con.commit()
    insert_table = "INSERT INTO jobs VALUES ( ?, ?, ?, ?, ?, ? )"
    values_ = list(
        zip(
            job_ids,
            job_posts,
            job_employers,
            locations,
            job_salaries,
            job_descriptions,
        )
    )
    print(values_)
    logger.info("Inserting rows")
    cur.executemany(insert_table, values_)
    con.commit()
    con.close()


if __name__ == "main":
    cf = _load_config()
    if (cf["linkedin_email"] or cf["linkedin_pwd"]) is None:
        logger.info("Incomplete credentials")
        exit()
    stopwords_dict = {word: 1 for word in stopwords.words("english")}
    job_ids = []
    job_posts = []
    job_employers = []
    locations = []
    job_descriptions = []
    job_salaries = []
    main()
