import codecs
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logging.basicConfig()


# Date entry
def date_input(months):
    date = input("Please enter desired date (DD.MM): ").split('.')

    # ValiDATE
    if int(date[1]) > 12 or int(date[1]) < 1:
        print("Entered month invalid.")
        date_input(months)
        return date
    elif int(date[0]) > months[int(date[1]) - 1] or int(date[0]) < 1:
        print("Entered date invalid.")
        date_input(months)
        return date
    return date


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
def adjust_length(name, max_len):
    if len(name) < max_len:
        name = (name + " " * max_len)[:max_len]
    return name


# Print results in table in prices.txt file
def fprint_result(names, prices, max_name_len, max_price_len):
    file = codecs.open("prices.txt", 'w+', 'utf-8')

    num_of_hashs = 15
    if not names:
        num_of_hashs = 30

    file.write("#" * (max_name_len + max_price_len + num_of_hashs) + "\r\n")
    file.write("#   " + adjust_length("Apartmani", max_name_len) + "   #   " + adjust_length("Cijene",
                                                                                             max_price_len) + "   #\r\n")
    file.write("#" * (max_name_len + max_price_len + num_of_hashs) + "\r\n")
    if names:
        for name, price in zip(names, prices):
            file.write("#   " + adjust_length(name, max_name_len) + "   #   " + adjust_length(price,
                                                                                              max_price_len) + "   #\r\n")
    else:
        file.write("#     No apartments found    #\r\n")
    file.write("#" * (max_name_len + max_price_len + num_of_hashs))

    file.close()
    return


def filter_result(names, prices):
    # noinspection PyBroadException
    try:
        with open('filter.txt', 'r') as file:
            filter_list = set(file.read().splitlines())
    except Exception:
        return names, prices

    if not filter_list:
        print("No filter set in filter.txt., ignoring filter.txt.")
        return names, prices

    print("Filter applied.")
    names_filtered = []
    prices_filtered = []
    for name, price in zip(names, prices):
        for item in filter_list:
            if name == item:
                names_filtered.append(name)
                prices_filtered.append(price)
    return names_filtered, prices_filtered


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

    print("Getting apartments names and prices...")

    names_unparsed = []
    prices_unparsed = []
    # Get unparsed names and prices from first page
    names_unparsed.append(webelement_to_text(driver.find_elements_by_class_name("sr-hotel__name")))
    prices_unparsed.append(webelement_to_text(driver.find_elements_by_class_name("bui-price-display__value")))

    # Find how many pages exists
    res_found = 0
    # noinspection PyBroadException
    try:
        # (Rijeka: 14 properties found).text.split(' ')[1] = 14
        res_found = int(driver.find_element_by_class_name("sr_header").text.split(' ')[1])
    except Exception:
        pass

    # Go through pages
    res_per_page = 25
    if res_found == '':
        pass
    elif res_found > res_per_page:
        print("Going through pages...")
        # First page url
        url = driver.current_url

        offset = res_per_page

        # Iterate through pages while there are no more listings
        while res_found > 0:
            res_found -= res_per_page

            # Go to next page using offset
            driver.get(url + '&offset=' + str(offset))

            names_unparsed.append(webelement_to_text(driver.find_elements_by_class_name("sr-hotel__name")))
            prices_unparsed.append(webelement_to_text(driver.find_elements_by_class_name("bui-price-display__value")))

            offset += 25

    # Separate items form item_max_len
    names_parsed = parse(names_unparsed)
    max_name_len = names_parsed[1]
    names_parsed = names_parsed[0]

    prices_parsed = parse(prices_unparsed)
    max_price_len = prices_parsed[1]
    prices_parsed = prices_parsed[0]

    # Filter only wanted apartments
    print("Filtering apartments...")
    result = filter_result(names_parsed, prices_parsed)

    # If filter applied, adjust max item length for prices.txt table dimensions
    if len(names_parsed) > len(result[0]):
        max_name_len = 0
        max_price_len = 0
        for name, price in zip(result[0], result[1]):
            if len(name) > max_name_len:
                max_name_len = len(name)
            if len(price) > max_price_len:
                max_price_len = len(price)

    # Separate names from prices
    names_parsed = result[0]
    prices_parsed = result[1]

    # Print to prices.txt
    print("Printing results to prices.txt...")
    fprint_result(names_parsed, prices_parsed, max_name_len, max_price_len)
    print("Results printed.")

    print("Closing Chromium...")
    driver.quit()


if __name__ == "__main__":
    main()
