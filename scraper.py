# -*- coding: utf-8 -*-
"""
Created on Sun Jun 26 21:27:27 2016

@author: EvgenyKashin
"""

from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime
from datetime import timedelta
import re
from collections import OrderedDict
import csv
import os.path
from selenium.webdriver.chrome import webdriver
import config


def make_telegram_request(params, method='sendMessage'):
    url = 'https://api.telegram.org/bot{}/{}'.format(config.TELEGRAM_TOKEN,
                                                     method)
    url += '?'
    for key, value in params.items():
        url += key + '=' + value + '&'
    requests.get(url)


def send_msg(text):
    params = {'chat_id': config.TELEGRAM_CHAT_ID,
              'text': text}
    make_telegram_request(params)


def get_trips_url(url, time_for_page, with_extension):
    trip_urls = []
    driver = None

    if with_extension:
        opt = webdriver.Options()
        opt.add_argument(r'user-data-dir=' + config.USER_DATA_DIR)
        opt.add_extension(config.EXTENSION_PATH)
        driver = webdriver.WebDriver(config.WEBDRIVER_PATH,
                                     chrome_options=opt)
        time.sleep(config.TIME_FOR_INIT)
    else:
        driver = webdriver.WebDriver(config.WEBDRIVER_PATH)

    try:
        driver.get(url)
        time.sleep(time_for_page)
        while True:
            elements = driver.find_elements_by_css_selector('.trip-search-oneresult')
            new_urls = [el.find_element_by_css_selector('meta').get_attribute('content') for el in elements]
            trip_urls.extend(new_urls)
            try:
                next_link = driver.find_element_by_css_selector('.next a')
                if '#' in next_link.get_attribute('href'):
                    break
            except:
                break
            next_link.click()
            time.sleep(time_for_page)
    except Exception as ex:
        driver.quit()
        raise ex
    finally:
        driver.quit()

    return trip_urls


def parse_time(time_str, today):
    hour_minute = re.search(r'[0-9]{2}:[0-9]{2}', time_str).group(0).split(':')
    is_today = 1 if re.search(r'Сегодня', time_str) is not None else 0
    is_tomorow = 1 if re.search(r'Завтра', time_str) is not None else 0
    if not is_today and not is_tomorow:
        dt = re.search(r'([0-9]{2}).?([\w]{3,})', time_str)
        day = dt.group(1)
        m = dt.group(2)
        if m == 'июня':
            month = 6
        elif m == 'июля':
            month = 7
        elif m == 'августа':
            month = 8
        elif m == 'сентября':
            month = 9
        elif m == 'октября':
            month = 10
        elif m == 'ноября':
            month = 11
        elif m == 'декабря':
            month = 12
        else:
            raise Exception('Wrong month')
        departure_date = datetime(today.year, month, int(day),
                                  int(hour_minute[0]), int(hour_minute[1]))
    else:
        departure_date = datetime.date(today) + timedelta(days=1 if is_tomorow
                                                          else 0)
        departure_date = datetime(departure_date.year, departure_date.month,
                                  departure_date.day,
                                  int(hour_minute[0]), int(hour_minute[1]))
    return str(departure_date)

# in 'with driver' added features:
# is_direct_route, driver_stars, comments_count, is_only_two


def get_trip_info(url):
    trip_info = OrderedDict()
    try:
        trip_info['trip_id'] = re.search(r'[0-9]{1,}$', url).group(0)
    except:
        trip_info['trip_id'] = None

    today = datetime.today()
    trip_info['parsing_date'] = str(today.day) + '.' + str(today.month) + ':'\
        + str(today.hour) + ':' + str(today.minute)

    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html5lib')

    title_ = soup.select('.RideName--title .RideName-location')
    num_title = int(len(title_) / 2)
    try:
        trip_info['title'] = ','.join([t.text for t in title_[:num_title]])
    except:
        trip_info['title'] = None

    date_info = soup.select_one('.RideDetails-publicationInfo .u-cell')
    try:
        trip_info['published_date'] = re.search(r'([0-9]{2}/[0-9]{2}/[0-9]{2})',
                                                date_info.text).group(0)
    except:
        trip_info['published_date'] = None

    try:
        trip_info['visits'] = int(re.search(r'[Просмотров,Просмотрено].?:?.?([0-9]{1,})',
                                  date_info.text).group(1))
    except:
        trip_info['visits'] = None

    price_ = soup.select_one('.Booking-price')
    try:
        price = re.split(r'\s', price_.text)
        trip_info['price'] = int(''.join(price[:-1]))
    except:
        trip_info['price'] = None

    passengers_free = soup.select_one('b')
    try:
        trip_info['passengers_free'] = passengers_free.text
    except:
        trip_info['passengers_free'] = None

    trip_info['passengers_max'] = len(soup.select('#maincontent .vertical-middle')) - 1

    departure_time_ = soup.select('strong span')
    try:
        trip_info['departure_time'] = parse_time(departure_time_[0].text.strip(),
                                                 today)
    except:
        trip_info['departure_time'] = None

    try:
        trip_info['driver_name'] = soup.select_one('.u-truncate a').text
    except:
        trip_info['driver_name'] = None

    driver_age_ = soup.select_one('div.ProfileCard-info')
    try:
        trip_info['driver_age'] = re.search(r'[0-9]{1,3}', driver_age_.text)\
                                            .group(0)
    except:
        trip_info['driver_age'] = None

    driver_status = None
    try:
        driver_status = soup.select('div + .ProfileCard-info')[0].text.strip()
    except:
        pass
    trip_info['driver_status'] = driver_status
    try:
        car_ = soup.select_one('.Profile-carDetails').text
        trip_info['car'] = re.search(r'(.{2,})\n', car_).group(1)
    except:
        trip_info['car'] = None
    driver_num_trips = 0
    try:
        trip_elements = soup.select('#maincontent .unstyled li')
        for el in trip_elements:
            match_ = re.search(r'([0-9]{1,}).{1,}поезд', el.text)
            try:
                driver_num_trips = int(match_.group(1))
            except:
                pass
    except:
        pass
    trip_info['driver_num_trips'] = driver_num_trips
    return trip_info


def get_trips_info_driver(urls, time_for_page, with_extension):
    if with_extension:
        opt = webdriver.Options()
        opt.add_argument(r'user-data-dir=' + config.USER_DATA_DIR)
        opt.add_extension(config.EXTENSION_PATH)
        driver = webdriver.WebDriver(config.WEBDRIVER_PATH,
                                     chrome_options=opt)
        time.sleep(config.TIME_FOR_INIT)
    else:
        driver = webdriver.WebDriver(config.WEBDRIVER_PATH)

    trips = []
    fails_urls = []
    for url in urls:
        try:
            trips.append(get_trip_info_driver(driver, url, time_for_page))
        except:
            fails_urls.append(url)
    driver.quit()

    return trips, fails_urls


def get_trip_info_driver(driver, url, time_for_page):
    trip_info = OrderedDict()

    try:
        driver.get(url)
        time.sleep(time_for_page)

        try:
            trip_info['trip_id'] = re.search(r'[0-9]{1,}$', url).group(0)
        except:
            trip_info['trip_id'] = None

        today = datetime.today()
        trip_info['parsing_date'] = str(today.day) + '.' + str(today.month) + ':'\
            + str(today.hour) + ':' + str(today.minute)
        
        title_ = driver.find_elements_by_css_selector('.RideName--title .RideName-location')
        num_title = int(len(title_) / 2)
        trip_info['is_direct_route'] = 1 if num_title == 2 else 0
        try:
            trip_info['title'] = ','.join([t.text
                                           for t in title_[:num_title]])
        except:
            trip_info['title'] = None

        date_info = driver.find_element_by_css_selector('.RideDetails-publicationInfo .u-cell')
        try:
            trip_info['published_date'] = re.search(r'([0-9]{2}/[0-9]{2}/[0-9]{2})',
                                                    date_info.text).group(0)
        except:
            trip_info['published_date'] = None

        try:
            trip_info['visits'] = int(re.search(r'[Просмотров,Просмотрено].?:?.?([0-9]{1,})',
                                      date_info.text).group(1))
        except:
            trip_info['visits'] = None

        price_ = driver.find_element_by_css_selector('.Booking-price')
        try:
            price = re.split(r'\s', price_.text)
            trip_info['price'] = int(''.join(price[:-1]))
        except:
            trip_info['price'] = None

        passengers_free = driver.find_element_by_css_selector('b')
        try:
            trip_info['passengers_free'] = passengers_free.text
        except:
            trip_info['passengers_free'] = None
    
        trip_info['passengers_max'] = len(driver.find_elements_by_css_selector('#maincontent .vertical-middle')) - 1
    
        departure_time_ = driver.find_elements_by_css_selector('strong span')
        try:
            trip_info['departure_time'] = parse_time(departure_time_[0].text.strip(),
                                                     today)
        except:
            trip_info['departure_time'] = None
    
        try:
            trip_info['driver_name'] = driver.find_element_by_css_selector('.u-truncate a').text
        except:
            trip_info['driver_name'] = None
    
        driver_age_ = driver.find_element_by_css_selector('div.ProfileCard-info')
        try:
            trip_info['driver_age'] = re.search(r'[0-9]{1,3}', driver_age_.text)\
                                                .group(0)
        except:
            trip_info['driver_age'] = None
    
        driver_status = None
        try:
            driver_status = driver.find_elements_by_css_selector('div + .ProfileCard-info')[0].text.strip()
        except:
            pass
        trip_info['driver_status'] = driver_status

        try:
            car_ = driver.find_element_by_css_selector('.Profile-carDetails').text
            trip_info['car'] = re.search(r'(.{2,})\n', car_).group(1)
        except:
            trip_info['car'] = None

        driver_num_trips = 0
        try:
            trip_elements = driver.find_elements_by_css_selector('#maincontent .unstyled li')
            for el in trip_elements:
                match_ = re.search(r'([0-9]{1,}).{1,}поезд', el.text)
                try:
                    driver_num_trips = int(match_.group(1))
                except:
                    pass
        except:
            pass
        trip_info['driver_num_trips'] = driver_num_trips

        try:
            stars_element = driver.find_element_by_css_selector('.u-textBold')
            stars = float(re.sub(',', '.', stars_element.text.split('/')[0]))
            trip_info['driver_stars'] = stars
        except:
            trip_info['driver_stars'] = None

        try:
            comments_elements = driver.find_element_by_css_selector('.tip .u-gray')
            match = re.search(r'[0-9]+', comments_elements.text)
            trip_info['comments_count'] = int(match.group(0))
        except:
            trip_info['comments_count'] = 0
        
        try:
            element = driver.find_element_by_css_selector('.u-clearfix~ .u-clearfix+ .u-clearfix span.RideDetails-infoValue')
            if element:
                trip_info['is_only_two'] = 1
            else:
                trip_info['is_only_two'] = 0
        except:
            trip_info['is_only_two'] = 0

    except Exception as ex:
        driver.quit()
        raise ex
    finally:
        pass
    return trip_info


def get_trips_info(urls):
    trips = []
    fails_urls = []
    for url in urls:
        try:
            trips.append(get_trip_info(url))
        except:
            fails_urls.append(url)
    return trips, fails_urls


def load_parse(urls, time_for_search_page, time_for_info_page, driver_for_all,
               with_extension):
    start_time = time.time()
    log_error = open(config.LOG_ERROR, 'a')
    log_success = open(config.LOG_SUCCESS, 'a')
    log_error.write('\n' + time.strftime('%x') + ' ' + time.strftime('%X') +
                    '\n')
    log_success.write('\n' + time.strftime('%x') + ' ' + time.strftime('%X') +
                      '\n')
    all_trips = []

    try:
        for url in urls:
            trips_urls = get_trips_url(url, time_for_search_page,
                                       with_extension)
            if len(trips_urls) == 0:
                raise Exception('Too little trips url')

            if driver_for_all:
                trips, fails = get_trips_info_driver(trips_urls,
                                                     time_for_info_page,
                                                     with_extension)
            else:
                trips, fails = get_trips_info(trips_urls)
            if len(trips) == 0:
                raise Exception('Too little trips')

            name = re.search(r'/([a-z-]{2,}/[a-z-]{2,})/#', url).group(1)
            name = re.sub(r'/', '_', name)
            print('url', name)
            print('urls', len(trips_urls))
            print('trips', len(trips))
            for trip in trips:
                trip['route'] = name
            all_trips.extend(trips)

            log_error.write(name + '\n')
            if len(fails) == 0:
                log_error.write('No error\n')
            else:
                for fail in fails:
                    log_error.write(fail)
                    log_error.write('\n')

            log_success.write(name + '\n')
            log_success.write(str(len(trips)) + ' loaded\n')
    except Exception as ex:
        log_error.write('Fatal error:\n' + str(ex) + '\n\n')
        log_error.close()
        log_success.close()
        raise ex

    is_write_header = False
    if not os.path.isfile(config.TRIPS_PATH):
        is_write_header = True
    with open(config.TRIPS_PATH, 'a', encoding='utf-8') as f:
        writer = csv.DictWriter(f, trips[0].keys(), delimiter=',',
                                lineterminator='\n')
        if is_write_header:
            writer.writeheader()
        writer.writerows(all_trips)

    log_error.write('\n')
    log_success.write('{} added\n'.format(len(all_trips)))
    log_success.write('{:.1f} seconds\n\n'
                      .format(time.time() - start_time))
    text_for_bot = datetime.now().strftime('%x %X') + ' '\
        + '{} added. '.format(len(all_trips)) \
        + '{:.1f} seconds\n'\
          .format(time.time() - start_time)
    send_msg(text_for_bot)
    log_error.close()
    log_success.close()


def do_scrape():
    try:
        print('Start at', datetime.now().strftime('%x %X'))
        load_parse(config.SEARCH_TRIP_URLS, config.TIME_FOR_SEARCH_PAGE,
                   config.TIME_FOR_INFO_PAGE,
                   config.WEBDRIVER_FOR_SINGLE_TRIP,
                   config.WITH_EXTENSION)
    except Exception as ex:
        print('restart')
        print(ex)
        with open(config.LOG_SUCCESS, 'a') as f:
            f.write('2nd try:\n')
        try:
            load_parse(config.SEARCH_TRIP_URLS,
                       config.TIME_FOR_SEARCH_PAGE + 30,
                       config.TIME_FOR_INFO_PAGE + 3,
                       config.WEBDRIVER_FOR_SINGLE_TRIP,
                       config.WITH_EXTENSION)
        except Exception as ex:
            raise ex


if __name__ == '__main__':
    do_scrape()
