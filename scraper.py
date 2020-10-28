import re
import datetime
from datetime import datetime, timedelta
import urllib3
import requests
from bs4 import BeautifulSoup
from abc import ABC
from requests import exceptions
import os
import dotenv
import sys



class Scraper(ABC):

    """
    Abstract base class inherited by all website scraping classes (fetch_html method)
    Setup proxy/API and request processing here.

    """

    def __init__(self):
        urllib3.disable_warnings()  # Needs to be disabled for scraperapi proxy to work (SSL related)
        dotenv.load_dotenv()
        SCRAPER_API_KEY = os.getenv('SCRAPERAPIKEY')
        self._proxy = {"https": SCRAPER_API_KEY}

    def _fetch_html(self, url):
        self.page = requests.get(url, verify=False, proxies=self._proxy, timeout=60)
        print(self.page.status_code)
        if self.page.status_code == 403:
            print('Maximum scraperAPI limit reached')
            sys.exit()
        elif self.page.status_code == 429:
            print('Maximum concurrency limit reached')
            sys.exit()
        self.page.raise_for_status()  # Raise exceptions if there are request problems
        self.html = BeautifulSoup(self.page.content, 'html.parser')
        return self.html


def word_convert(alist):
    kws = {'full': 'fullTime', 'part': 'partTime', 'intern': 'internship', 'permanent': 'permanent',
           'casual': 'casual', 'sub': 'subContract', 'contract': 'contract', 'temp': 'temporary', 'fly': 'flyInOut'}
    for kw in kws:
        for index, word in enumerate(alist):
            if kw in word.lower():
                alist[index] = kws[kw]
                continue
    return alist


class IndeedScraper(Scraper):
    """
    Web scraper for Indeed. Will parse html from indeed and output into json format containing various job details.
    Any tinkering of the requests/proxy/error catching is configured in the Scraper class.

    _base_url(str): base url where search queries are attached. Current search parameter is: 'work visa'
    _job_url(str): base url for where individual job pages are located. Job ID is concatenated to the url.
    _job_links(list): list of links containing job url
    html_parser(dict): Company, logo, location, title, salary, position, date posted, description
    """

    def __init__(self):
        super().__init__()
        self.base_url = 'https://au.indeed.com/jobs?q=work+visa&l=Australia&sort=date'
        self.job_url = 'https://au.indeed.com/viewjob?jk='
        self.reference = 'indeed'

    def html_parser(self, link):
        html = self._fetch_html(link)
        job_container = html.find('div', class_='jobsearch-JobComponent')

        # Get job offer id from the link
        if link:
            pattern = 'jk=.*'
            job_offer_id = re.search(pattern, link).group()[3:]
        else:
            job_offer_id = None

        # Get job offer title
        try:
            job_title = job_container.find('h1', class_='jobsearch-JobInfoHeader-title').text
        except AttributeError:
            job_title = None

        # Get company name
        try:
            company = job_container.find('div', class_='icl-u-lg-mr--sm icl-u-xs-mr--xs').text
        except AttributeError:
            company = None

        # Get company location
        try:
            locations = job_container.find('div', class_='jobsearch-InlineCompanyRating').select('div')[-1].text
            states = ['VIC', 'NSW', 'SA', 'QLD', 'TAS', 'WA', 'ACT', 'NT']

            location = locations.split()
            postcode = None
            state = None
            suburb = ''
            for i in location:
                if re.search(r'\d', i):
                    postcode = i
                elif i in states:
                    state = i
                else:
                    suburb += i + ' '
            suburb = suburb.strip()

        except AttributeError:
            suburb = None
            state = None
            postcode = None

        # Grabbing salary and position_status
        try:
            sal_and_pos = job_container.find('div', class_='jobsearch-JobMetadataHeader-item').findAll('span')
            # If there are two elements , grab both.
            if len(sal_and_pos) == 2:
                salary = sal_and_pos[0].text
                position_status = sal_and_pos[1].text.replace(u'\xa0', '')
                # Hyphen only exists when there are two elements.
                pattern = '-.*?'
                position_status = re.sub(pattern, '', position_status, count=1).replace(' ', '').split(',')
            # Otherwise, if the single element contains digits, assign to salary.
            elif bool(re.search(r'\d', sal_and_pos[0].text)):
                salary = sal_and_pos[0].text
                position_status = None
            # If no digits, assign to position status instead.
            else:
                salary = None

                position_status = sal_and_pos[0].text.replace(u'\xa0', '').replace(' ', '').split(',')
        # When salary & position doesn't exist
        except AttributeError:
            salary = None
            position_status = None

        if position_status:
            position_status = word_convert(position_status)

        # Get company logo src
        try:
            logo_container = html.find('img', class_='jobsearch-CompanyAvatar-image')
            company_logo = logo_container['src']
            logo_alt = logo_container['alt']

        # Company doesn't have logo uploaded
        except TypeError:
            company_logo = None
            logo_alt = None

        # Grab date posted
        # try:
        #     date_posted = job_container.find('div', class_='jobsearch-JobMetadataFooter').text
        #     temp = re.findall(r'\d+', date_posted)  # Check if number exists
        #
        #     # If number doesn't exist, job is posted today.
        #     date_posted = datetime.strftime(datetime.today(), '%d-%m-%Y') if not temp else \
        #         datetime.strftime(datetime.today() - timedelta(days=int(temp[0])), '%d-%m-%Y')
        # except AttributeError:
        #     date_posted = None


        # Grab date posted epoch
        try:
            date_posted = job_container.find('div', class_='jobsearch-JobMetadataFooter').text
            temp = re.findall(r'\d+', date_posted)  # Check if number exists
            # If number doesn't exist, job is posted today.
            date_posted = datetime.today().timestamp() if not temp else \
                (datetime.today() - timedelta(days=int(temp[0]))).timestamp()
        except AttributeError:
            date_posted = None


        # Grab job description
        try:
            job_description = job_container.find('div', id='jobDescriptionText').text
        except AttributeError:
            job_description = None

        job_offer = {
            'title': job_title,
            'id': job_offer_id,
            'externalId': None,
            'workingVisa': True,
            'company': {
                'name': company,
                'id': '1',     # Our end unique company id
                'logo': {
                    'src': company_logo,
                    'alt': logo_alt
                },
                'details': None     # leave blank for now
            },
            'positions': position_status,
            'salary': salary,
            'datePosted': date_posted,
            'dateExpiring': None,
            'description': job_description,
            'location': {
                'suburb': suburb,
                'state': state,
                'postcode': postcode,
                'description': None
            },
            'link': link,
            'reference': self.reference,
            'categories': None
        }

        return job_offer

    def job_links(self, num_jobs):  # num jobs = 25
        """
        Method used to generate the individual job links
        Replaceable if js rendering is available.

        :param num_jobs: number of job links to be returned
        :return: _job_links(list)
        """
        job_list = set()
        query = ''
        pages, remaining_jobs = divmod(num_jobs, 15)
        for page in range(pages+1):
            try:
                results = self._fetch_html(self.base_url + query).find(id='resultsCol')
                jobs = results.findAll(class_='jobsearch-SerpJobCard unifiedRow row result')
                temp = remaining_jobs if page == pages else 15
                for job in jobs[:temp]:
                    job_id = job.attrs['data-jk']
                    link = self.job_url + job_id
                    job_list.add(link)
                query = f'&start={page * 10 + 10}'  # page 2 on indeed is &start=10
            except exceptions.HTTPError:
                print('HTTP error, skipping job')
                continue
            except exceptions.ConnectionError:
                print('Connection Error, skipping job')
                continue
            except exceptions.Timeout:
                print('Requests timed out, try re-checking your links.')
                continue

        return list(job_list)

    def today_job_links(self):
        """
        Grabs all job links that are posted today
        Same as job_links method except it scrapes until there are no more jobs for today.

        :return: job links in a list
        """
        job_list = set()
        query = ''
        posted_today = True
        page = 0
        while posted_today:
            try:
                results = self._fetch_html(self.base_url + query).find(id='resultsCol')
                jobs = results.findAll(class_='jobsearch-SerpJobCard unifiedRow row result')
                for job in jobs:
                    try:
                        date = job.find('span', class_='date').text
                    except AttributeError:
                        continue

                    if not re.search(r'\d', date):  # No numbers, i.e. today or just now posted.
                        job_id = job.attrs['data-jk']
                        link = self.job_url + job_id
                        job_list.add(link)
                    else:
                        print('No more jobs posted today')
                        posted_today = False
                        return job_list

                page += 1
                query = f'&start={page * 10 + 10}'  # page 2 on indeed is &start=10
            except exceptions.HTTPError:
                print('HTTP error, skipping job')
                continue
            except exceptions.ConnectionError:
                print('Connection Error, skipping job')
                continue
            except exceptions.Timeout:
                print('Requests timed out, try re-checking your links.')
                continue


class SeekScraper(Scraper):
    def __init__(self):
        super().__init__()


class LinkedinScraper(Scraper):
    def __init__(self):
        super().__init__()


if __name__ == '__main__':
    indeed = IndeedScraper()
    job_list = indeed.today_job_links()
    print(job_list)
    print(len(job_list))