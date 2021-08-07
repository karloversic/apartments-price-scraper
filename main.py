import codecs
import logging
from selenium import webdriver

logging.basicConfig()


# Set up search query
def search(driver):
    # City
    driver.find_element_by_name("ss").send_keys("Rijeka")
    # Dates table
    driver.find_element_by_xpath('//*[@id="frm"]/div[1]/div[2]/div[1]/div[2]/div/div/div/div/span').click()
    # Today
    driver.find_element_by_class_name('bui-calendar__date--today').click()
    # Search button
    driver.find_element_by_xpath('//*[@id="frm"]/div[1]/div[4]/div[2]/button').click()


# Retrieve names from current page
def get_names(driver):
    aparts_name = driver.find_elements_by_class_name("sr-hotel__name")
    aparts_name_text = []
    for name in aparts_name:
        aparts_name_text.append(name.text)
    return aparts_name_text


# Retrieve prices from current page
def get_prices(driver):
    aparts_price = driver.find_elements_by_class_name("bui-price-display__value")
    aparts_price_text = []
    for price in aparts_price:
        aparts_price_text.append(price.text)
    return aparts_price_text


# Convert 2D list to 1D list
def parse(list_unparsed):
    max_len = -1
    list_parsed = []
    for items in list_unparsed:
        for item in items:
            list_parsed.append(item)

            if len(item) > max_len:
                max_len = len(item)
    return list_parsed, max_len


# Adjust length to max_len
def adjust_length(name, max_len):
    if len(name) < max_len:
        name = (name + " " * max_len)[:max_len]
    return name


# Print results in table in prices.txt file
def print_result(names, prices, max_name_len, max_price_len):
    file = codecs.open("prices.txt", 'w+', 'utf-8')

    file.write("#" * (max_name_len + max_price_len + 15) + "\n")
    file.write("#   " + adjust_length("Apartmani", max_name_len) + "   #   " + adjust_length("Cijene",
                                                                                             max_price_len) + "   #" + "\n")
    file.write("#" * (max_name_len + max_price_len + 15) + "\n")
    for name, price in zip(names, prices):
        file.write("#   " + adjust_length(name, max_name_len) + "   #   " + adjust_length(price,
                                                                                          max_price_len) + "   #" + "\n")
    file.write("#" * (max_name_len + max_price_len + 15))

    file.close()


def main():
    # Open booking.com in chromium
    driver = webdriver.Chrome()
    driver.get("https://www.booking.com")

    # Search for Rijeka and today's date
    search(driver)

    names_unparsed = []
    prices_unparsed = []

    # Get unparsed names and prices from first page
    names_unparsed.append(get_names(driver))
    prices_unparsed.append(get_prices(driver))

    # Find how many pages exists
    res_info = ""
    # noinspection PyBroadException
    try:
        res_info = driver.find_element_by_class_name("results-meta")
    except Exception:
        pass

    # Go through pages
    if res_info != "":
        res_sum = int(res_info.text.split(' ')[1])

        # First page url
        url = driver.current_url

        res_per_page = 25
        offset = res_per_page

        # Iterate through pages while there are no more listings
        while res_sum > 0:
            res_sum -= res_per_page

            # Go to next page using offset
            driver.get(url + '&offset=' + str(offset))

            names_unparsed.append(get_names(driver))
            prices_unparsed.append(get_prices(driver))

            offset += 25

    # Separate items form item_max_len
    names_parsed = parse(names_unparsed)
    max_name_len = names_parsed[1]
    names_parsed = names_parsed[0]

    prices_parsed = parse(prices_unparsed)
    max_price_len = prices_parsed[1]
    prices_parsed = prices_parsed[0]

    print_result(names_parsed, prices_parsed, max_name_len, max_price_len)

    driver.quit()


if __name__ == "__main__":
    main()
