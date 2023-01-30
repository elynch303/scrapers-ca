from utils import CSVScraper


class KingstonPersonScraper(CSVScraper):
    # https://opendatakingston.cityofkingston.ca/explore/dataset/council-contact-list/
    csv_url = "https://opendatakingston.cityofkingston.ca/explore/dataset/council-contact-list/download/?format=csv&timezone=America/New_York&use_labels_for_header=true"
    delimiter = ";"
