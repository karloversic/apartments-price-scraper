import codecs
import logging
import sys
from math import ceil
from operator import attrgetter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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
    today = driver.find_element_by_class_name('bui-calendar__date--today').get_attribute("data-date").split("-")
    today_year = int(today[0])
    today_month = int(today[1])

    # Check for leap year
    if today_year % 4 == 0:
        months[1] = 29

    date = input("Please enter desired date (DD.MM): ").split('.')

    # ValiDATE
    success = 0
    while success != 1:
        if len(date) == 1:
            print('Entered day and month invalid or missing dot.')
            date = input("Please enter desired date (DD.MM): ").split('.')
            continue
        elif date[1] == '' or int(date[1]) > 12 or int(date[1]) < 1:
            print("Entered month invalid.")
            date = input("Please enter desired date (DD.MM): ").split('.')
            continue
        elif date[0] == '' or int(date[0]) > months[int(date[1]) - 1] or int(date[0]) < 1:
            print("Entered day invalid.")
            date = input("Please enter desired date (DD.MM): ").split('.')
            continue
        else:
            success = 1

    # Get all calendar entries that are valid
    cal_entries = webelement_to_text(driver.find_elements_by_class_name('bui-calendar__date'))

    # Check on which calendar pane (1st or 2nd) is desired month
    additional_days = -1
    if int(date[1]) != today_month:
        additional_days = 41

    print("Locating desired date's webelement...")
    # Find desired date on calendar
    blanks = -1
    for entry in cal_entries:
        # Skip empty cells, and skip current month if next one is desired
        if entry == '' or blanks < additional_days:
            blanks += 1
            continue
        elif entry == date[0]:
            # driver.find_elements_by_class_name('bui-calendar__date')[int(date[0])].click()
            driver.find_elements_by_class_name('bui-calendar__date')[int(date[0]) + blanks].click()
            break
    return


# Set up search query
def search(driver):
    # City
    driver.find_element_by_name("ss").send_keys("Rijeka")
    # Dates table
    driver.find_element_by_xpath('//*[@id="frm"]/div[1]/div[2]/div[1]/div[2]/div/div/div/div/span').click()
    # Date
    get_date(driver)
    # Search button
    print("Search submitted.")
    driver.find_element_by_class_name('-submit-button').click()
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
    file = codecs.open("prices.txt", 'w+', 'utf-8')

    num_of_hashs = 15
    if not apartments:
        num_of_hashs = 31

    file.write("#" * (name_len + price_len + num_of_hashs) + "\r\n")
    file.write("#   " + adjust_length("Apartmani", name_len) + "   #   " + adjust_length("Cijene",
                                                                                         price_len) + "  #\r\n")
    file.write("#" * (name_len + price_len + num_of_hashs) + "\r\n")
    if apartments:
        for apartment in apartments:
            file.write("#   " + adjust_length(apartment.name, name_len) + "   #   " + apartment.currency + " " + adjust_length(str(apartment.price),
                                                                                                                               price_len) + " #\r\n")
    else:
        file.write("#    No apartments found    #\r\n")
    file.write("#" * (name_len + price_len + num_of_hashs))

    file.close()
    print("Results printed.")
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
    print("Opening Chromium...")
    # Open booking.com in headless Chromium
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
        res_found = int(driver.find_element_by_class_name("sr_header").text.split(' ')[1])
        print("Results found: " + str(res_found) + " (" + str(ceil(res_found / 25)) + " pages)")
    except Exception:
        pass

    print("Getting apartments names and prices...")
    print("Going through page(s)...")
    if res_found != 0:
        print(" ... page 1/" + str(ceil(res_found / 25)))

    names_unparsed = []
    prices_unparsed = []
    # Get unparsed names and prices from first page
    names_unparsed.append(webelement_to_text(driver.find_elements_by_class_name("sr-hotel__name")))
    prices_unparsed.append(webelement_to_text(driver.find_elements_by_class_name("bui-price-display__value")))

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

            names_unparsed.append(webelement_to_text(driver.find_elements_by_class_name("sr-hotel__name")))
            prices_unparsed.append(webelement_to_text(driver.find_elements_by_class_name("bui-price-display__value")))

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
