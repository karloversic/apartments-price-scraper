# Apartments price scraper
Scrapes "www.booking.com" for prices of (specific) apartments, and saves the data in `prices.txt` in table.

### Usage
After starting browser, date input is required in format `DD.MM`


### Requirements
For scraper to  work, [chromedriver](https://chromedriver.chromium.org/) is required.


### Specify apartments (optional)
To specify which apartments to look for, create `filter.txt`, and paste apartments name into it, separated by newline, e.g.:

    Apartment Eclipse
    Residence apartments
    Studio City
    ...


## Notes
Both `chromedriver.exe` and `filter.txt` has to be in root folder (`apartments-price-scraper/`) in order to work.


