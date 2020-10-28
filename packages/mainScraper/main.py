from requests import exceptions
import json
from packages.mainScraper import scraper


class Main:

    """
    Main class that the user will interact with.

    get_data: High level method and the only method that the user should interact with. Outputs in json format the
    following fields: Company, logo, location, title, salary, position, date posted, description.
    ** Currently stores as a json file in the project directory.

    """
    def __init__(self):
        self._job_data = []

    def get_data(self, website: str, num_jobs: int = 0):
        """
        :param website: Website to scrape
        :param num_jobs: number of jobs to scrape. It will scrape all of today's job by default.
        """
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
                links = scrape.job_links(num_jobs) if num_jobs else scrape.today_job_links()
                for link in links:
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
    # check line 41 to see how much to scrape.
    s = Main()
    s.get_data('indeed', 1)





