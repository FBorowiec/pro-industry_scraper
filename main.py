from config.config_handler import ParametersHandler
from data_types.vacancy import Vacancy
from scraper.pro_industry_scraper import ProIndustryScraper

if __name__ == "__main__":
    scraper: ProIndustryScraper = ProIndustryScraper()
    results: list[Vacancy] = scraper.parse_site()
    if ParametersHandler().get_params()["save_to_file"]:
        scraper.save_to_csv(results)
