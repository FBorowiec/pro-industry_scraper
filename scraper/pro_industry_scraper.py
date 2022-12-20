import logging
from time import sleep
from typing import Any, MutableMapping
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup, element
from requests.adapters import HTTPAdapter
from requests.sessions import Session
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from tenacity import retry
from tenacity.wait import wait_exponential
from urllib3.util import Retry

from config.config_handler import ParametersHandler, PresetsHandler
from data_types.position_details import PositionDetails
from data_types.vacancy import Vacancy
from utils.flatten_dict import flatten_dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(message)s")


class ProIndustryScraper:
    PARAMS: dict[str, Any] = ParametersHandler().get_params()
    PRESETS: dict[str, Any] = PresetsHandler().get_presets()

    def __init__(self) -> None:
        self.session: Session = self._init_session()
        self.browser: Firefox | None = None
        self._reset_browser()

    def _init_session(self) -> Session:
        session: Session = Session()
        retries: Retry = Retry(
            connect=self.PARAMS["retry"]["connect"],
            read=self.PARAMS["retry"]["read"],
            redirect=self.PARAMS["retry"]["read"],
        )

        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.headers.update({"User-agent": self.PARAMS["agent"]})

        return session

    def _reset_browser(self) -> None:
        browser_options: Options = Options()
        browser_options.add_argument("--headless")
        self.browser = Firefox(options=browser_options)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=5))
    def get_page_soup(self, page: int) -> BeautifulSoup:
        suffix: str = f"?{self.PARAMS['pagination']}={page}"
        url: str = urljoin(self.PARAMS["base_url"], suffix)

        self._reset_browser()
        assert self.browser is not None, "Failure in intializing the Browser!"
        with self.browser as browser:
            browser.get(url)
            page_source: str = browser.page_source
            page_soup: BeautifulSoup = BeautifulSoup(page_source, "html.parser")

        return page_soup

    @retry(wait=wait_exponential(multiplier=1, min=2, max=5))
    def get_position_soup(self, position_url: str) -> BeautifulSoup:
        response: requests.Response = self.session.get(position_url)
        position_soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")

        return position_soup

    def get_job_details(self, ul: element.Tag) -> list[str]:
        job_details: list[str] = []
        for li in ul.find_all("li"):
            span: element.Tag = li.find_all("span")[0]
            text: str = span.text.strip()
            job_details.append(text)
        assert len(job_details) > 7, "Invalid job details obtained!"

        return job_details

    def parse_position(self, url: str) -> PositionDetails | None:
        position_soup: BeautifulSoup = self.get_position_soup(url)

        try:
            ul: element.Tag = position_soup.find_all(
                "ul", class_=self.PRESETS["auxiliary_page"]["job_details"]
            )[0]
        except IndexError as e:
            logging.error(f"Error in parsing the position details:\n{e}")
            return None
        job_details: list[str] = self.get_job_details(ul)

        return PositionDetails(
            location=job_details[0],
            salary_range=job_details[1],
            job_type=job_details[2],
            contract_type=job_details[3],
            position_name=job_details[4],
            industry=job_details[5],
            required_education=job_details[6],
            time_length=job_details[7] if len(job_details) > 8 else None,
            hours=job_details[-1],
        )

    def parse_page(self, soup: BeautifulSoup) -> list[Vacancy]:
        positions_results: element.ResultSet[Any] = soup.find_all(
            "div", {"class": self.PRESETS["results"]["position"]}
        )

        vacancies: list[Vacancy] = []
        for result in positions_results:
            for row in result.find_all("a"):
                raw_url: str = row.get("href")
                if "vacature/" in raw_url:
                    url: str = str(urljoin(self.PARAMS["base_url"], raw_url))
                    position_details: PositionDetails | None = self.parse_position(url)
                    if not position_details:
                        continue
                    sleep(self.PARAMS["sleep_time"])  # don't overload the server
                    vacancy: Vacancy = Vacancy(
                        title=row.find_all(
                            "h2", class_=self.PRESETS["results"]["title"]
                        )[0].text,
                        brief_description=row.find_all(
                            "span", class_=self.PRESETS["results"]["brief_description"]
                        )[0].text,
                        full_description=row.find_all(
                            "div", class_=self.PRESETS["results"]["full_description"]
                        )[0].text.strip(),
                        position_details=position_details,
                        url=url,
                    )
                    if self.PARAMS["verbose_logging"]:
                        logging.info(f"New position parsed:\n{vacancy}")
                    vacancies.append(vacancy)

        return vacancies

    def save_to_csv(self, results: list[Vacancy]) -> None:
        results_dict: list[MutableMapping[Any, Any]] = [
            flatten_dict(vacancy.dict()) for vacancy in results
        ]
        results_df: pd.DataFrame = pd.DataFrame(results_dict)
        results_df.to_csv(self.PARAMS["output_file"], index=False)

    def parse_site(self) -> list[Vacancy]:
        logging.info("Starting parsing...")
        first_page_soup: BeautifulSoup = self.get_page_soup(1)
        page_results: list[Vacancy] = self.parse_page(first_page_soup)
        results: list[Vacancy] = page_results

        page_num: int = 2
        while len(page_results) > 0:
            logging.info(f"Parsing {page_num} page...")
            page_soup: BeautifulSoup = self.get_page_soup(page_num)
            page_results = self.parse_page(page_soup)
            page_num += 1
            if page_results:
                results.extend(page_results)
            if self.PARAMS["page_limit"] and page_num >= self.PARAMS["page_limit"]:
                break

        return results
