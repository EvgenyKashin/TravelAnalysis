# TravelAnalysis

This repo contains the python project for scraping and analysing a travel website.

## Usage
A folder called driver contain binary file chromedriver which is using by selenium. On linux and windows it is differ. I'm using selenium because a search page of site is building by JavaScript and it can not be reached via BeautifulSoup. There are two ways for scraping:

1. Sheduled to run a script scraper.py (using cron)

2. Run main_loop.py

The second way have some drawback for me. I used my home computer and sometimes I had electrical failures. If computer rebooted it have to run main_loop.py every times again. But if you use server it will be better to use the second way.

All downloaded data saved at .csv file after every successful iteration and after that it is sending message to Teleram chanel via Telegram Bot API. Also all events are written to log folder.

## Settings
Look in config.py for a full list of all the configuration options. Also you should create a file called private.py with secret parameters:
* SEARCH_TRIP_URLS - list of urls for scraping
* TELEGRAM_TOKEN - your token for telegram bot
* TELEGRAM_CHAT_ID - id of your Telegram chat