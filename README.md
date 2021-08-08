# Apartments price scraper
Scrapes "www.booking.com" for prices of (specific) apartments, and saves the data in .txt table.

### Requirements
For scraper to  work, [chromedriver](https://chromedriver.chromium.org/) is required.


### Specify apartments (optional)
To specify which apartments to look for, create `apartments_list.txt`, and paste apartments name into it, separated by newline, e.g.:

    Apartment Eclipse
    Residence apartments
    Studio City
    ...


## Notes
Both `chromedriver.exe` and `apartments_list.txt` has to be in root folder (`apartments-price-scraper/`) in order to work.


