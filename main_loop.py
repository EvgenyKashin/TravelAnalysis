from scraper import do_scrape
import config
import time
import sys
import traceback

if __name__ == '__main__':
    while True:
        try:
            do_scrape()
        except KeyboardInterrupt:
            print('Exit')
            sys.exit(1)
        except Exception as ex:
            print(ex)
            traceback.print_exc()
        time.sleep(config.SLEEP_TIME)
