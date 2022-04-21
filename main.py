import codecs
import logging
import re
import sys
from math import ceil
from operator import attrgetter

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig()


# Convert Selenium webelement to string
def webelement_to_text(item_list):
    list_text = []
    for item in item_list:
        list_text.append(item.text)
    return list_text


# Select desired date on calendar
def get_date(driver):
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Get "today", today's year, and today's month
    today = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'bui-calendar__date--today'))).get_attribute('data-date').split(
        "-")
    today_year = int(today[0])
    today_month = int(today[1])
    today_day = int(today[2])

    # Check for leap year
    if today_year % 4 == 0:
        months[1] = 29

    def str_to_char(word):
        return [char for char in word]

    def date_input():
        user_input = input('Please enter desired date (DD.MM): ')

        return user_input

    valid = 0
    date = date_input()
    while valid != 1:
        if len(date) != 5 or not re.search('\d\d.\d\d', date):
            print('Input invalid, please use (DD.MM) format.')
            date = date_input()
        else:
            day = int(str_to_char(date)[0] + str_to_char(date)[1])
            month = int(str_to_char(date)[3] + str_to_char(date)[4])

            if month > 12 or month < 1:
                print('Entered month invalid.')
                date = date_input()
            elif day > months[month - 1] or day < 1 or (day < today_day and month == today_month):
                print('Entered day invalid.')
                date = date_input()
            else:
                valid = 1

    # Get all calendar entries that are valid
    driver.find_elements(by=By.CLASS_NAME, value='bui-calendar__date')[4].click()
    cal_entries = webelement_to_text(driver.find_elements(by=By.CLASS_NAME, value='bui-calendar__date'))

    # Check on which calendar pane (1st or 2nd) is desired month
    additional_days = -1
    if month != today_month:
        additional_days = 41

    # Find desired date on calendar
    print("Locating desired date's webelement...")
    blanks = -1
    for entry in cal_entries:
        # Skip empty cells, and skip current month if next one is desired
        if entry == '' or blanks < additional_days:
            blanks += 1
            continue
        elif int(entry) == day:
            driver.find_elements(by=By.CLASS_NAME, value='bui-calendar__date')[day + blanks].click()
            break
    return


# Set up search query
def search(driver):
    # Accept cookies
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))).click()

    # Select city
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.NAME, 'ss'))).send_keys('Rijeka')

    # Date table
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'xp__dates'))).click()

    # Date
    get_date(driver)

    # Search button
    print('Search submitted.')
    driver.find_element(by=By.CLASS_NAME, value='-submit-button').click()

    # Set currency to EUR
    driver.get(driver.current_url + ';selected_currency=EUR')


# Convert 2D list to 1D list
def parse(list_unparsed):
    max_len = -1
    list_parsed = []
    for items in list_unparsed:
        for item in items:
            list_parsed.append(item)

            # Get max item length to know prices.txt table dimensions
            if len(item) > max_len:
                max_len = len(item)
    return list_parsed, max_len


# Adjust length to max_len
def adjust_length(item, max_len):
    if len(item) < max_len:
        item = (item + " " * max_len)[:max_len]
    return item


# Print results in table in prices.txt file
def fprint_result(apartments, name_len, price_len):
    file = codecs.open('prices.txt', 'w+', 'utf-8')

    num_of_hashs = 15
    if not apartments:
        num_of_hashs = 31

    file.write('#' * (name_len + price_len + num_of_hashs) + "\r\n")
    file.write('#   ' + adjust_length('Apartmani', name_len) + '   #   ' + adjust_length('Cijene',
                                                                                         price_len) + "  #\r\n")
    file.write("#" * (name_len + price_len + num_of_hashs) + "\r\n")
    if apartments:
        for apartment in apartments:
            file.write(
                '#   ' + adjust_length(apartment.name, name_len) + '   #   ' + apartment.currency + " " + adjust_length(
                    str(apartment.price),
                    price_len) + ' #\r\n')
    else:
        file.write('#    No apartments found    #\r\n')
    file.write('#' * (name_len + price_len + num_of_hashs))

    file.close()
    print('Results printed.')
    return


def sort_and_filter(apartments):
    # Sort by price
    apartments = sorted(apartments, key=attrgetter('price'), reverse=True)
    print("Apartments sorted.")

    # noinspection PyBroadException
    try:
        with open('filter.txt', 'r') as file:
            filter_list = set(file.read().splitlines())
    except Exception:
        print("File filter.txt. not found, no filter applied.")
        return apartments

    if not filter_list:
        print("No filter set in filter.txt., no filter applied.")
        return apartments

    apartments_filtered = []
    for apartment in apartments:
        for item in filter_list:
            if apartment.name == item:
                apartments_filtered.append(apartment)
    print("Apartments filtered.")
    return apartments_filtered


class MaxLength:
    def __init__(self, name, price):
        self.name = name
        self.price = price


class Apartment:
    def __init__(self, name, currency, price):
        self.name = name
        self.currency = currency
        self.price = int(price)


def main():
    # Open booking.com in headless Chromium
    print("Opening booking.com...")
    options = Options()
    options.add_argument('headless')
    options.add_argument('disable-gpu')
    options.add_argument("window-size=1920,1080")
    # Bypass "headless" mode block
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    options.add_argument(f'user-agent={user_agent}')

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.booking.com")

    # Search for Rijeka and desired date
    print("Setting up search...")
    search(driver)

    # Find how many pages exists
    res_found = 0
    # noinspection PyBroadException
    try:
        # (Rijeka: 14 properties found).text.split(' ')[1] = 14
        res_found = int(driver.find_element(by=By.CLASS_NAME, value='e1f827110f').text.split(' ')[1])
        print("Results found: " + str(res_found) + " (" + str(ceil(res_found / 25)) + " pages)")
    except Exception:
        print("No results found.")
        pass

    print("Getting apartments names and prices...")
    print("Going through page(s)...")
    if res_found != 0:
        print(" ... page 1/" + str(ceil(res_found / 25)))

    names_unparsed = []
    prices_unparsed = []
    # Get unparsed names and prices from first page
    names_unparsed.append(webelement_to_text(driver.find_elements(by=By.CLASS_NAME, value='a23c043802')))
    prices_unparsed.append(webelement_to_text(driver.find_elements(by=By.CLASS_NAME, value='bd73d13072')))

    # Go through pages
    res_per_page = 25
    if res_found == '':
        pass
    elif res_found > res_per_page:
        # First page url
        url = driver.current_url

        # Iterate through pages while there are no more listings
        offset = res_per_page
        res_left = res_found
        page = 2
        while res_left > 0:
            res_left -= res_per_page

            # Go to next page using offset
            driver.get(url + '&offset=' + str(offset))
            if page <= ceil(res_found / 25):
                print(" ... page " + str(page) + "/" + str(ceil(res_found / 25)))

            names_unparsed.append(webelement_to_text(driver.find_elements(by=By.CLASS_NAME, value='a23c043802')))
            prices_unparsed.append(
                webelement_to_text(driver.find_elements(by=By.CLASS_NAME, value='bd73d13072')))

            offset += 25
            page += 1

    # Separate items form item max length
    names_parsed = parse(names_unparsed)
    prices_parsed = parse(prices_unparsed)

    length = MaxLength(names_parsed[1], prices_parsed[1])

    names_parsed = names_parsed[0]
    prices_parsed = prices_parsed[0]

    apartments = []
    for name, price in zip(names_parsed, prices_parsed):
        # Split price into currency and value and store them together with name in apartments_object
        cur = price.split(' ')[0]
        tmp_price = price.split(' ')[1]
        apartments.append(Apartment(name, cur, int(tmp_price)))

    print("Sorting and filtering apartments...")
    apartments_saf = sort_and_filter(apartments)

    # If filter applied, adjust max item length for prices.txt table dimensions
    if sys.getsizeof(apartments) > sys.getsizeof(apartments_saf):
        max_name_len = 0
        max_price_len = 0
        for apartment in apartments_saf:
            if len(apartment.name) > max_name_len:
                max_name_len = len(apartment.name)
            if len(str(apartment.price)) > max_price_len:
                max_price_len = len(str(apartment.price))

    # Print to prices.txt
    print("Printing results to prices.txt...")
    fprint_result(apartments_saf, length.name, length.price)

    print("Closing Chromium...")
    driver.quit()


if __name__ == "__main__":
    main()
