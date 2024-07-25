from bot import Bot
import traceback
from dotenv import load_dotenv
import re
from pathlib import Path
import requests
import logging
import os
import time
from slugify import slugify
from datetime import datetime
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from enum import Enum
from dateutil.relativedelta import relativedelta
load_dotenv('config.env')


class Dirs(Enum):
    OUTPUT = "output"
    LOGS = f"{OUTPUT}/logs"
    IMGS = f"{OUTPUT}/imgs"
    EXCEL = f"{OUTPUT}/excel"


class Timeouts(Enum):
    SECOND_1 = 1.0
    SECOND_3 = 3.0
    SECOND_5 = 5.0
    SECOND_10 = 10.0
    SECOND_15 = 15.0
    SECOND_20 = 20.0
    SECOND_30 = 30.0
    SECOND_60 = 60.0
    SECOND_90 = 90.0


class Elements(Enum):
    SEARCH_ICON = "//header//div[contains(@class, 'search-trigger')]/button"
    FORM = "//form[@role='search']"
    SEARCH_BAR = f"{FORM}//input[contains(@class, 'search-bar')]"
    SORT_SELECTION = "//select[@id='search-sort-option']"
    ARTICLE = "//article"
    SHOW_MORE = "//button[contains(@class, 'show-more-button')]"
    LOADING = "//div[@class='loading-animation']"
    FOOTER = "//footer[@class='site-footer']"
    RESULTS = "//div[@class='search-result__list']"


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
log_file_name = f'{Dirs.LOGS.value}/log-file.log'
os.makedirs(os.path.dirname(log_file_name), exist_ok=True)
file_handler = logging.FileHandler(log_file_name, mode='a')
file_handler.setLevel(logging.DEBUG)


class Robot(Bot):
    RETRY_MAX = 5
    LOGGER = logging.getLogger(os.getenv("LOGGER"))
    LOGGER.addHandler(console_handler)
    LOGGER.addHandler(file_handler)

    def __init__(self):
        self.RETRY_MAX = None
        self.driver = Selenium()
        self.excel = Files()
        self.limit_date = None
        self.start = datetime.now()
        self.error_counter = self.__new_counter()
        self.error = 0
        self.wait_time = Timeouts.SECOND_5.value
        self.timeout = Timeouts.SECOND_15.value
        self.page_load = Timeouts.SECOND_30.value
        self.load_strategy = None
        self.url = None
        self.query = None
        self.topic = None
        self.months = None
        self.article_counter = self.__new_counter()
        self.articles = 0
        self.should_stop = False
        self.sheet_name = None
        self.excel_file = None
        self.chrome_opened = False
        self.excel_opened = False
        self.curr_idx = 1

    def retry(n=RETRY_MAX):
        def decorator(func):
            def wrapper(*args, **kwargs):
                for i in range(n):
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        Robot.LOGGER.error(
                            f"""{func.__name__} failed with error:
                                {type(e)} - {e}"""
                        )
                        if i == n - 1:
                            Robot.LOGGER.error(traceback.print_exc())
                            raise e
            return wrapper
        return decorator

    def set_config(self):
        try:
            q = os.getenv("QUERY", "")
            retry = os.getenv("RETRY_MAX", Robot.RETRY_MAX)
            self.sheet_name = os.getenv("SHEET_NAME", "data")
            self.RETRY_MAX = int(retry)
            self.url = os.getenv("URL")
            self.query = slugify(q)
            self.topic = os.getenv("TOPIC")
            self.months = os.getenv("MONTHS")
            self.load_strategy = os.getenv("LOAD_STRATEGY", "normal")
            print(
                self.query,
                self.months,
                self.topic,
                self.RETRY_MAX,
                self.url)
            Robot.LOGGER.info("Variables and configs set up.")
        except Exception as e:
            Robot.LOGGER.error(f"Error setting up configs. {e}")
            Robot.LOGGER.error(traceback.print_exc())
            raise e

    def set_env(self):
        try:
            self.set_config()
            self.__create_dirs()
            self.excel_file = self.__create_excel_file()
            self.driver.close_all_browsers()
            self.__open_chrome()
            self.chrome_opened = True
            self.limit_date = self.__get_limit_date()
            Robot.LOGGER.info("Environment set up.")
        except Exception as e:
            Robot.LOGGER.error(f"Error setting up environment. {e}")
            Robot.LOGGER.error(traceback.print_exc())
            raise e

    def init(self):
        try:
            self.set_env()
            self.excel.close_workbook()
            self.excel.open_workbook(self.excel_file)
            self.excel_opened = True
            self.excel.set_active_worksheet(self.sheet_name)
            Robot.LOGGER.info("Environment initialized.")
        except Exception as e:
            Robot.LOGGER.error(f"Error initializing environment. {e}")
            Robot.LOGGER.error(traceback.print_exc())
            raise e

    def get_work_item(self):
        pass

    def set_work_item_status(self):
        pass

    def handle_exception(self, e):
        Robot.LOGGER.error(e)
        self.error = self.error_counter()
        if self.error < self.RETRY_MAX:
            self.run()
        else:
            self.finish_job_with_exception(e)

    def run(self):
        ready = False
        try:
            self.init()
            ready = True
        except Exception as e:
            Robot.LOGGER.error(f"Error initializing Environment. {e}")

        if ready:
            try:
                self.start_job()
            except Exception as e:
                Robot.LOGGER.error(f"Error running job. {e}")
                self.handle_exception(e)
            else:
                self.finish_job()

    def stop(self):
        Robot.LOGGER.info("Automation must stop processing.")
        self.should_stop = True

    def next_job(self):
        pass

    def start_job(self):
        Robot.LOGGER.info("Started job execution")
        self.excel.open_workbook(self.excel_file)
        Robot.LOGGER.info("Excel sheet opened")
        self.__click_search_icon()
        self.__input_search()
        self.__send_search_form()
        self.__sort_search_content()
        self.__process_articles()

    def finish_job(self):
        self.excel.save_workbook()
        self.excel.close_workbook()
        self.driver.close_all_browsers()
        Robot.LOGGER.info(
            f"Automation read {self.articles} articles"
        )

    def finish_job_with_exception(self, e):
        if self.excel_opened:
            self.excel.save_workbook()
            self.excel.close_workbook()

        if self.chrome_opened:
            self.driver.close_all_browsers()
        Robot.LOGGER.error(
            f"""After {self.error} attempts,
                the job was finished with exception: {e}"""
        )

    def __new_counter(self):
        count: int = 0

        def increment() -> int:
            nonlocal count
            count += 1
            return count

        return increment

    def __get_limit_date(self):
        months = int(self.months)
        current_date = self.start
        delta = months - 1 if months - 1 >= 0 else 0
        limit_date = current_date - relativedelta(months=delta)
        first_day_of_month = limit_date.replace(day=1)
        return first_day_of_month.date()

    def __create_excel_file(self):
        file_name = self.start.strftime('%Y-%m-%d_%H-%M')
        sheet = os.getenv("SHEET_NAME", "data")
        file = f"{Dirs.EXCEL.value}/{file_name}.xlsx"
        self.excel.create_workbook(
            path=file,
            sheet_name=sheet,
        )
        self.excel.append_rows_to_worksheet(
            name=sheet,
            header=True,
            content=[
                [
                    "title",
                    "date",
                    "description",
                    "picture_filename",
                    "phrase_count_in_title",
                    "money_related"
                ],
            ],
        )
        self.excel.save_workbook(file)
        return file

    def __download_img(self, link, file_name):
        img_dir = Path(Dirs.IMGS.value)
        save_to = None
        att = 0
        for _ in range(Robot.RETRY_MAX):
            response = requests.get(link)
            if response.status_code == 200:
                save_to = str(img_dir.joinpath(f"{file_name}.jpg"))
                with open(save_to, 'wb') as file:
                    file.write(response.content)
                Robot.LOGGER.info(f"Image successfully downloaded: {save_to}")
                break
            else:
                att += 1
                Robot.LOGGER.warn(
                    f"Failed to download image. Status code: \
                    {response.status_code}"
                )
        return save_to

        if att == Robot.RETRY_MAX - 1:
            Robot.LOGGER.error(
                f"Unable to download image {link} after\
                    {Robot.RETRY_MAX} attempts"
            )
        return save_to

    @retry()
    def __next_page(self):
        if self.driver.does_page_contain_element(
            locator=Elements.SHOW_MORE.value
        ):
            self.driver.scroll_element_into_view(Elements.FOOTER.value)
            self.driver.wait_and_click_button(Elements.SHOW_MORE.value)
            self.driver.wait_until_page_contains_element(
                locator=Elements.LOADING.value,
                timeout=Timeouts.SECOND_10.value
            )
            self.driver.wait_until_page_does_not_contain_element(
                locator=Elements.LOADING.value,
                timeout=Timeouts.SECOND_10.value
            )
            Robot.LOGGER.info("Next page loaded.")
            return True
        else:
            Robot.LOGGER.info("Could not load next page.")
            return False

    def __validate_url(self):
        if not self.driver.is_location(self.url):
            Robot.LOGGER.info(f"Navigating to {self.url}")
            self.driver.go_to(self.url)
            return self.driver.is_location(self.url)
        Robot.LOGGER.info(f"Driver in correct url: {self.url}")
        return True

    @retry()
    def __click_search_icon(self):
        try:
            self.driver.click_element_when_clickable(
                Elements.SEARCH_ICON.value,
                timeout=Timeouts.SECOND_5.value
            )
            self.driver.wait_until_page_contains_element(
                Elements.SEARCH_BAR.value,
                timeout=Timeouts.SECOND_5.value
            )
            assert self.driver.does_page_contain_element(
                Elements.SEARCH_BAR.value
            )
            Robot.LOGGER.info("clicked search icon.")
        except AssertionError as e:
            self.driver.go_to(self.url)
            self.driver.maximize_browser_window()
            self.driver.wait_until_page_contains_element(
                Elements.SEARCH_ICON.value,
                Timeouts.SECOND_10.value
            )
            Robot.LOGGER.error(traceback.print_exc())
            raise e

    @retry()
    def __input_search(self):
        self.driver.input_text(
            Elements.SEARCH_BAR.value,
            self.query.replace("-", " ")
        )
        assert self.driver.get_value(
            Elements.SEARCH_BAR.value
        ) == self.query.replace("-", " ")
        Robot.LOGGER.info("Query typed in search-bar")

    @retry()
    def __send_search_form(self):
        try:
            self.driver.submit_form(Elements.FORM.value)
            Robot.LOGGER.info(f"Searched for {self.query}")
            assert lambda self: self.driver.wait_until_page_contains(
                Elements.RESULTS.value,
                Timeouts.SECOND_20.value
            )
            Robot.LOGGER.info("Search results loaded.")
        except AssertionError as e:
            self.__input_search()
            Robot.LOGGER.error(traceback.print_exc())
            raise e

    def __create_dirs(self):
        for dir in Dirs:
            os.makedirs(name=dir.value, mode=0o777, exist_ok=True)

    @retry()
    def __open_chrome(self):
        try:
            opts = {
                "capabilities": {
                    "pageLoadStrategy": self.load_strategy,
                    "timeouts": {
                        "implicit": self.wait_time * 1000,
                        "pageLoad": self.page_load * 1000,
                        "script": self.timeout * 1000,
                    }
                }
            }
            Robot.LOGGER.debug("Browser options set up.")
            self.driver.open_browser(
                url=self.url,
                alias="MAIN",
                browser="chrome",
                options=opts
            )
            Robot.LOGGER.debug("Browser opened")
            self.driver.maximize_browser_window()
            Robot.LOGGER.debug("Browser maximized")
            time.sleep(Timeouts.SECOND_10.value)
            assert self.__validate_url()
            Robot.LOGGER.debug("Browser URL validated")
        except AssertionError as e:
            self.driver.close_all_browsers()
            Robot.LOGGER.error(traceback.print_exc())
            raise e

    @retry()
    def __sort_search_content(self):
        try:
            self.driver.wait_until_page_contains_element(
                locator=Elements.SORT_SELECTION.value,
                timeout=Timeouts.SECOND_5.value
            )
            self.driver.select_from_list_by_value(
                Elements.SORT_SELECTION.value,
                "date"
            )
            self.driver.wait_until_page_contains_element(
                locator=Elements.RESULTS.value,
                timeout=Timeouts.SECOND_10.value
            )
            assert self.driver.get_selected_list_value(
                Elements.SORT_SELECTION.value
            ) == "date"
            Robot.LOGGER.info("Sorted results by date.")
        except Exception as e:
            self.driver.reload_page()
            Robot.LOGGER.error(traceback.print_exc())
            raise e

    @retry()
    def __process_articles(self):
        try:
            self.driver.wait_until_page_contains_element(
                locator=Elements.RESULTS.value,
                timeout=Timeouts.SECOND_10.value
            )
            while not self.should_stop:
                Robot.LOGGER.info(f"Processing article {self.curr_idx}")
                article = f"{Elements.ARTICLE.value}[{self.curr_idx}]"
                self.curr_idx += 1
                if not self.driver.does_page_contain_element(article):
                    Robot.LOGGER.info(f"Article {self.curr_idx} not found.")
                    next = self.__next_page()
                    if not next:
                        break
                obj = self.__get_article_info(article)
                if obj is None:
                    continue
                self.__add_data_to_excel(obj)
                self.articles = self.article_counter()
        except Exception as e:
            self.driver.reload_page()
            self.__reach_to_current_article()
            Robot.LOGGER.error(traceback.print_exc())
            raise e

    def __add_data_to_excel(self, obj):
        self.excel.append_rows_to_worksheet(
            name=self.sheet_name,
            content=[
                [
                    obj["title"],
                    obj["date"],
                    obj["description"],
                    obj["file"],
                    obj["count"],
                    obj["matches-currency"]
                ]
            ]
        )

    def __parse_date_string(self, date_str):
        regex = r"([0-9]{1,2} \b\w{3}\b [0-9]{4})"
        match = re.search(regex, date_str)
        if match:
            date_part = match.group(1)
            article_date = datetime.strptime(date_part, "%d %b %Y").date()
            return article_date
        else:
            raise ValueError(f"Date string format is incorrect: {date_str}")

    def __is_currency_related(self, txt):
        regex = r'(\$(\d{1,3}[.,]{0,1})*)|((\d{1,3}[.,]{0,1})*\s(dollars|USD))'
        return bool(re.findall(regex, txt))

    def __get_article_info(self, article):
        self.driver.scroll_element_into_view(article)
        link = self.driver.get_element_attribute(f"{article}//h3//a", "href")
        Robot.LOGGER.info(f"Started processing article {link}")
        title = self.driver.get_element_attribute(
            f"{article}//h3//a", "innerText"
        )
        try:
            date_string = self.driver.get_element_attribute(
                f"{article}//footer//span[@aria-hidden]",
                "innerText"
            )
        except Exception:
            Robot.LOGGER.info(f"Article {link} is not news.")
            return None
        try:
            article_date = self.__parse_date_string(date_string)
        except ValueError as e:
            Robot.LOGGER.info(f"Unable to define date for article {link}: {e}")
            return None
        pub_date = article_date.strftime("%Y-%m-%d")
        if article_date < self.limit_date:
            Robot.LOGGER.info(f"Article {link} is out of date range.")
            self.stop()
            return None
        summary = self.driver.get_element_attribute(
            f"{article}//p",
            "innerText"
        )
        img = self.driver.get_element_attribute(f"{article}//img", "src")
        alt = self.driver.get_element_attribute(f"{article}//img", "alt")
        count = str(link).count(self.query)
        matches_curr = (
            self.__is_currency_related(summary)
            or self.__is_currency_related(title)
        )
        slug_str = str(link).split('/')[-1]
        file = self.__download_img(img, slug_str) or ""
        obj = {
            "title": title,
            "url": link,
            "description": summary,
            "img-alt": alt,
            "image": img,
            "date": pub_date,
            "count": count,
            "matches-currency": matches_curr,
            "slug": slug_str,
            "file": file
        }
        Robot.LOGGER.info(f"All information obtained for article {link}")
        return obj

    def __reach_to_current_article(self):
        Robot.LOGGER.info(f"Searching for article index {self.curr_idx}")
        assert self.driver.wait_until_page_contains_element(
            Elements.RESULTS.value,
            Timeouts.SECOND_30.value
        )
        while not self.driver.does_page_contain(
            f"{Elements.ARTICLE.value}[{self.curr_idx}]"
        ):
            next = self.__next_page()
            if not next:
                break
        Robot.LOGGER.info(f"Reached page containing article {self.curr_idx}")


if __name__ == "__main__":
    robot = Robot()
    robot.run()
