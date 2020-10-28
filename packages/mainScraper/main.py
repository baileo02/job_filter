from requests import exceptions
import json
from packages.mainScraper import scraper as scraper


class Main:

    """
    Main class that the user will interact with.
    Configure proxy and requests parameters here

    fetch_html: Method to return html content given url.

    get_data: High level method and the only method that the user should interact with. Outputs in json format the
    following fields: Company, logo, location, title, salary, position, date posted, description.
    ** Currently stores as a json file in the project directory.

    """
    def __init__(self):
        self._job_data = []

    def get_data(self, website: str, num_jobs: int):
        scrape = None

        if website.lower() == 'indeed':  # Use indeed scraper
            scrape = scraper.IndeedScraper()

        elif website.lower() == 'seek':
            scrape = scraper.SeekScraper()
            # Seek html parsing function

        elif website.lower() == 'linkedin':
            scrape = scraper.LinkedinScraper()
            # Linkedin html parsing function
        else:
            print(f'{website} not available. Did you misspell?')

        if scrape:
            try:
                for link in scrape.job_links(num_jobs):     # Grabs job links returns as list
                    try:
                        self._job_data.append(scrape.html_parser(link))
                    except exceptions.HTTPError:
                        print('HTTP error, skipping job')
                        continue
                    except exceptions.ConnectionError:
                        print('Connection Error, skipping job')
                        continue
                    except exceptions.Timeout:
                        print('Requests timed out, try re-checking your links.')
                        continue

            finally:
                with open("../../job_data.json", "w") as write_file:
                    json.dump(self._job_data, write_file)





if __name__ == '__main__':
    s = Main()
    s.get_data('indeed', 1)
    # with open('job_data.json', 'r') as rf:
    #     j = json.load(rf)
    #     for i in j:
    #         print(i['Link'])

    #todo filter function

