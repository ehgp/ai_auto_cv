"""Linked In Jobs.

Selenium Job that will apply to jobs for you on LinkedIn.
For educational purposes only, not responsible for blocked accounts.
"""
import logging
import logging.config
import os
import random
import re
import shutil
import sqlite3
import string
import time
from datetime import datetime as dt
from os import listdir
from os.path import isfile, join
from pathlib import Path

import chromedriver_autoinstaller
import nltk
import pandas as pd
import yaml
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from transformers import pipeline

import log

nltk.download("stopwords", quiet=True)
# Paths
path = Path(os.path.dirname(os.path.abspath(__file__)))
root_path = Path(path).parent.parent
logger = log.setup_logger(__name__)


def _remove_html_tags(text):
    """Remove html tags from a string."""
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def clean_text(text):
    """Clean text by removing HTML tags, punctuation, stopwords, and symbols."""
    # Initialize a summarization pipeline
    summarizer = pipeline('summarization', model='t5-small')

    # Summarize the input text
    summarized = summarizer(text, max_length=300, min_length=150, do_sample=False)
    summarized_text = summarized[0]['summary_text']

    # Remove HTML tags
    soup = BeautifulSoup(summarized_text, "html.parser")
    clean_text = soup.get_text()

    # Remove punctuation
    clean_text = clean_text.translate(str.maketrans("", "", string.punctuation))

    # Convert to lowercase
    clean_text = clean_text.lower()

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    words = clean_text.split()
    clean_words = [word for word in words if word not in stop_words]
    clean_text = " ".join(clean_words)

    # Remove symbols
    clean_text = re.sub(r"[^a-zA-Z0-9\s]", "", clean_text)

    return clean_text


def _save_html_to_file(response, title):
    """Save response to response.html."""
    if "job_main" in title:
        path_to_save = Path(root_path, "responses", "linkedin", "main")
    else:
        path_to_save = Path(root_path, "responses", "linkedin", "job")
    with open(
        Path(path_to_save, f"{title}.html"),
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
    config_path = os.path.join(path, "parameters_linkedin.yaml")
    with open(config_path, "r") as config_file:
        config_defs = yaml.safe_load(config_file.read())

    if config_defs.values() is None:
        raise ValueError("Yaml file is empty")

    if (config_defs["linkedin_email"] or config_defs["linkedin_pwd"]) is None:
        raise ValueError("Incomplete linkedin credentials")

    return config_defs


def store_in_db(jobs):
    """Store jobs in database."""
    con = sqlite3.connect(f"{root_path}/jobs.db")
    cur = con.cursor()
    create_table = """CREATE TABLE IF NOT EXISTS jobs \
        (job_ids text, job_posts text, job_employers text, \
        job_locations text, job_workplace_types text, job_salaries text, job_hirer_info text, job_descriptions text)"""
    logger.info("Creating Table jobs")
    cur.execute(create_table)
    con.commit()
    insert_table = "INSERT INTO jobs VALUES ( :job_id, :job_post, :job_employer, :job_location, :job_workplace_type, :job_salary, :job_hirer_info, :job_description )"
    for job in jobs:
        logger.info(job)
        logger.info("Inserting row")
        cur.execute(insert_table, job)
    con.commit()
    con.close()


class SeleniumLI:
    """Selenium LinkedIn.

    This will store a cookie session of your login and will initialize a driver.
    """

    def __init__(self) -> None:
        """Initialize."""
        logger.info("Starting LinkedIn Job Scraper")
        self.cf = _load_config()
        logger.info("Configure ChromeOptions")
        chromedriver_autoinstaller.install()
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

        self.driver = webdriver.Chrome(options=self.options)

    def scrape_ez(self, jobs: dict) -> None:
        """Execute Easy Apply Automation."""
        logger.info("Log In")
        self.driver.get(self.cf["li_login"])
        time.sleep(random.randint(3, 5))
        self.driver.refresh()
        time.sleep(random.randint(3, 5))
        self.driver.refresh()
        time.sleep(random.uniform(0.15, 0.4))
        self.driver.find_element_by_id("username").send_keys(self.cf["linkedin_email"])
        time.sleep(random.uniform(0.15, 0.4))
        self.driver.find_element_by_id("password").send_keys(self.cf["linkedin_pwd"])
        time.sleep(random.uniform(0.15, 0.4))
        (
            WebDriverWait(self.driver, 10)
            .until(
                EC.element_to_be_clickable((By.XPATH, self.cf["xpath"]["login_btn"]))
            )
            .click()
        )
        time.sleep(random.uniform(0.15, 0.4))
        # for i in range(0, 240, 24):
        for i in range(0, 1):
            self.job_ids = []
            time.sleep(random.randint(3, 5))
            self.driver.get(
                self.cf["search_ezapp"].format(
                    keywords=self.cf["keywords"].replace(" ", "%20"),
                    location=self.cf["location"].replace(" ", "%20"),
                    page=i,
                )
            )
            time.sleep(random.randint(5, 10))
            content = self.driver.execute_script(self.cf['xpath']['get_html'])
            soup = BeautifulSoup(content, "lxml")
            _save_html_to_file(content, f"linkedin_job_main_page_{i}")
            for link in soup.findAll(
                "li",
                class_=re.compile(self.cf['xpath']['get_all_jobs']),
            ):
                self.job_ids.append(link.get(self.cf['xpath']['get_job_id']))
            for job_id in self.job_ids:
                time.sleep(random.randint(3, 5))
                self.driver.get(self.cf["search_job"].format(job_id=job_id))
                time.sleep(random.randint(5, 10))
                content = self.driver.execute_script(self.cf['xpath']['get_html'])
                soup = BeautifulSoup(content, "lxml")
                _save_html_to_file(content, f"linkedin_job_id_{job_id}")
                logger.info(f"Job ID: {job_id}")
                # Job Post Name
                try:
                    job_post = _remove_html_tags(
                        soup.find(
                            "button", class_=re.compile(self.cf['xpath']['job_post'])
                        )
                        .text.replace("Save", "")
                        .replace("\n", " ")
                        .replace("  ", "")
                        .strip()
                    ).split(" at ")[0]

                except Exception as e:
                    logger.error(e)
                    job_post = None
                logger.info(f"Job Post Name: {job_post}")

                # Job Employer Name
                try:
                    job_employer = _remove_html_tags(
                        soup.find(
                            "button", class_=re.compile(self.cf['xpath']['job_post'])
                        )
                        .text.replace("Save", "")
                        .replace("\n", " ")
                        .replace("  ", "")
                        .strip()
                    ).split(" at ")[1]

                except Exception as e:
                    logger.error(e)
                    job_employer = None
                logger.info(f"Job Employer: {job_employer}")

                # Job Location
                try:
                    job_location = _remove_html_tags(
                        soup.find(
                            "span",
                            class_=re.compile(self.cf['xpath']['job_location']),
                        )
                        .text.replace("\n", " ")
                        .replace("  ", "")
                        .strip()
                    )

                except Exception as e:
                    logger.error(e)
                    job_location = None
                logger.info(f"Job Location: {job_location}")

                # Job Description
                try:
                    job_description = clean_text(
                        soup.find(
                            "div",
                            class_=re.compile(self.cf['xpath']['job_description']),
                            recursive=True,
                        ).get_text()
                    )

                except Exception as e:
                    logger.error(e)
                    job_description = None
                logger.info(f"Job Description: {job_description}")

                # Job Salary
                try:
                    job_salary = (
                        soup.find(
                            "div",
                            id_=re.compile(self.cf['xpath']['job_salary']),
                        )
                        .text.replace("\n", "")
                        .replace("  ", "")
                    )
                except Exception as e:
                    logger.error(e)
                    try:
                        job_salary = (
                            soup.find("a", class_="app-aware-link", href="#SALARY")
                            .text.replace("\n", "")
                            .replace("  ", "")
                        )
                    except Exception as e:
                        logger.error(e)
                        job_salary = None
                logger.info(f"Job Salary: {job_salary}")

                # Job Workplace Type
                try:
                    job_workplace_type = (
                        soup.find(
                            "span",
                            class_=re.compile(self.cf['xpath']['job_workplace_type']),
                        )
                        .text.replace("\n", "")
                        .replace("  ", "")
                    )
                except Exception as e:
                    logger.error(e)
                    job_workplace_type = None
                logger.info(f"Job Workplace Type: {job_workplace_type}")

                # Job Hirer Info
                try:
                    job_hirer_info = (
                        soup.find(
                            "div", class_=re.compile(self.cf['xpath']['job_hirer_info'])
                        )
                        .find("a")
                        .get("href")
                    )
                except Exception as e:
                    logger.error(e)
                    job_hirer_info = None
                logger.info(f"Job Hirer Info: {job_hirer_info}")

                jobs.append(
                    {
                        "job_id": job_id,
                        "job_post": job_post,
                        "job_employer": job_employer,
                        "job_location": job_location,
                        "job_workplace_type": job_workplace_type,
                        "job_salary": job_salary,
                        "job_hirer_info": job_hirer_info,
                        "job_description": job_description,
                    }
                )

        self.driver.quit()
        return jobs


def test_ez(path: str):
    """Test function to extract job information from html file."""
    cf = _load_config()
    content = _read_html(path)
    soup = BeautifulSoup(content, "lxml")
    # Job Post Name
    try:
        job_post = _remove_html_tags(
            soup.find("button", class_=re.compile(cf['xpath']['job_post']))
            .text.replace("Save", "")
            .replace("\n", " ")
            .replace("  ", "")
            .strip()
        ).split(" at ")[0]

    except Exception as e:
        logger.error(e)
        job_post = None
    logger.info(f"Job Post Name: {job_post}")

    # Job Employer Name
    try:
        job_employer = _remove_html_tags(
            soup.find("button", class_=re.compile(cf['xpath']['job_post']))
            .text.replace("Save", "")
            .replace("\n", " ")
            .replace("  ", "")
            .strip()
        ).split(" at ")[1]

    except Exception as e:
        logger.error(e)
        job_employer = None
    logger.info(f"Job Employer: {job_employer}")

    # Job Location
    try:
        job_location = _remove_html_tags(
            soup.find(
                "span",
                class_=re.compile(cf['xpath']['job_location']),
            )
            .text.replace("\n", " ")
            .replace("  ", "")
            .strip()
        )

    except Exception as e:
        logger.error(e)
        job_location = None
    logger.info(f"Job Location: {job_location}")

    # Job Description
    try:
        job_description = clean_text(
            soup.find(
                "div",
                class_=re.compile(cf['xpath']['job_description']),
                recursive=True,
            ).get_text()
        )

    except Exception as e:
        logger.error(e)
        job_description = None
    logger.info(f"Job Description: {job_description}")

    # Job Salary
    try:
        job_salary = (
            soup.find(
                "div",
                id_=re.compile(cf['xpath']['job_salary']),
            )
            .text.replace("\n", "")
            .replace("  ", "")
        )
    except Exception as e:
        logger.error(e)
        try:
            job_salary = (
                soup.find("a", class_="app-aware-link", href="#SALARY")
                .text.replace("\n", "")
                .replace("  ", "")
            )
        except Exception as e:
            logger.error(e)
            job_salary = None
    logger.info(f"Job Salary: {job_salary}")

    # Job Workplace Type
    try:
        job_workplace_type = (
            soup.find(
                "span",
                class_=re.compile(cf['xpath']['job_workplace_type']),
            )
            .text.replace("\n", "")
            .replace("  ", "")
        )
    except Exception as e:
        logger.error(e)
        job_workplace_type = None
    logger.info(f"Job Workplace Type: {job_workplace_type}")

    # Job Hirer Info
    try:
        job_hirer_info = (
            soup.find("div", class_=re.compile(cf['xpath']['job_hirer_info']))
            .find("a")
            .get("href")
        )
    except Exception as e:
        logger.error(e)
        job_hirer_info = None
    logger.info(f"Job Hirer Info: {job_hirer_info}")


def scrape_linkedin():
    """Scrape LinkedIn for jobs."""
    test_ez(f"{root_path}/responses/linkedin/job/linkedin_job_id_3612931486.html")
    # jobs = []
    # sli = SeleniumLI()
    # jobs = sli.scrape_ez(jobs)
    # store_in_db(jobs)


if __name__ == "__main__":
    scrape_linkedin()
