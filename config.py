# pause between scraping, every 1 hour
SLEEP_TIME = 3600

# time for scraping page with search results
TIME_FOR_SEARCH_PAGE = 15

# time for scraping page with info about trip
TIME_FOR_INFO_PAGE = 3

# time for webdriver to init, because of hala extension
TIME_FOR_INIT = 5

# flag for using webdriver for single trip
# if value is False, will be used BeautifulSoup
WEBDRIVER_FOR_SINGLE_TRIP = True

# enable chrome extension from EXTENSION_PATH
WITH_EXTENSION = True

# path to settings for chromedriver
USER_DATA_DIR = 'driver/settings'

# path to extension for chromedriver
EXTENSION_PATH = 'driver/hola.crx'

WEBDRIVER_PATH = 'driver/chromedriver'

# store result
TRIPS_PATH = 'data/trips.csv'

# store log
LOG_SUCCESS = 'log/success.txt'
LOG_ERROR = 'log/error.txt'

# notifications enable
SEND_TO_TELEGRAM = True

# TELEGRAM_TOKEN, SEARCH_TRIP_URLS, TELEGRAM_CHAT_ID in private.py
try:
    from private import *
except Exception:
    pass
