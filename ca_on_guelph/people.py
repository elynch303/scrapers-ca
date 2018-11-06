from utils import CSVScraper


class GuelphPersonScraper(CSVScraper):
    # http://data.open.guelph.ca/dataset/city-of-guelph-contacts
    csv_url = 'http://data.open.guelph.ca/datafiles/guelph-mayor-and-councillors-contact-information-2014-2018.csv'
    many_posts_per_area = True
