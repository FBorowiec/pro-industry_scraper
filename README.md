# ProIndustry scraper

_A project I made to show how I would approach web scraping. Here the biggest
issue was the fact that the developers behind the `pro-industry` website are
rendering a table of 15 job offers in `JavaScript` instead of a plain `html`.
Well I guess a world without `JavaScript` would make a lot of RAM producers
unhappy._

## Description

The vacancy list is dynamically created using `JavaScript` which doesn't allow
for fast scraping as we have to wait for `JavaScript` to render the table.
Moreover, it is impossible to directly download the `html` data and scrape it using
`BeautifulSoup` as the results wouldn't contain the table.
Therefore, I used `Selenium` with a `Firefox` webdriver to allow
the website to dynamically generate the `JavaScript` elements and then
feed them to `BS4`.

The output results is a CSV file containing all the open positions.

__Notes__:

* User parameters can be changed inside `config/parameters.yaml`
* The attached `results.csv` contains the results of the first 10 pages
* The `pyproject.toml` with `mypy`, `pylint` and more configurations is **not** included
* The application can easily be `Docker`-ized
* Before generating a `DataFrame` converted then in a `CSV`, the output is a list
  of `pydantic` models. It would be easy to feed it to an appropriately configured
  `PostgreSQL` database
* Each new page needs to be properly rendered, which significantly slows down the
  scraping of the site

## Setup with `pipenv`

This project uses a virtual environment. Please make sure to enable it by
running:

```shell
pip install pipenv
pipenv shell
pipenv --python /usr/bin/python3
pipenv install -r requirements.txt
```

## User inputs

The user settings can be changed inside the `config/parameters.yaml` file:

* The default logging of each new page is enabled by default.
* The page_limit is set to `10`

## How to run

Please make sure you're within the `main.py` file level.

```shell
python3 main.py
```

This will generate a `results.csv` CSV file inside your current directory.
