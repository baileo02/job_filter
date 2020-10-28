import re
import datetime
from datetime import datetime, timedelta
import urllib3
import requests
from bs4 import BeautifulSoup
from abc import ABC
from requests import exceptions



class Scraper(ABC):

    def __init__(self):
        urllib3.disable_warnings()  # Needs to be disabled for scraperapi proxy to work (SSL related)
        self._proxy = {"https": "http://scraperapi:92b0ea1d03d948a699aa1cad4cd334e1@proxy-server.scraperapi.com:8001"}

    def _fetch_html(self, url):
        page = html = None
        self.page = requests.get(url, proxies=self._proxy, verify=False, timeout=60)
        print(self.page.status_code)
        self.page.raise_for_status()  # Raise exceptions if there are request problems
        self.html = BeautifulSoup(self.page.content, 'html.parser')
        return self.html


class IndeedScraper(Scraper):
    """
    Web scraper for Indeed.
    _base_url(str): base url where search queries are attached
    _job_url(str): base url for where individual job pages are located. Job ID is concatenated to the url.
    _job_links(list): list of links containing job url
    html_parser(dict): Company, logo, location, title, salary, position, date posted, description
    """

    def __init__(self):
        super().__init__()
        self.base_url = 'https://au.indeed.com/jobs?q=work+visa&l=Australia&sort=date'
        self.job_url = 'https://au.indeed.com/viewjob?jk='

    def html_parser(self, link):
        html = self._fetch_html(link)
        job_container = html.find('div', class_='jobsearch-JobComponent')

        try:
            job_title = job_container.find('h1', class_='jobsearch-JobInfoHeader-title').text
        except AttributeError:
            job_title = None

        try:
            company = job_container.find('div', class_='icl-u-lg-mr--sm icl-u-xs-mr--xs').text
        except AttributeError:
            company = None

        try:
            location = job_container.find('div', class_='jobsearch-InlineCompanyRating').select('div')[-1].text
        except AttributeError:
            location = None

        # Grabbing salary and position_status
        try:
            sal_and_pos = job_container.find('div', class_='jobsearch-JobMetadataHeader-item').findAll('span')
            # If there are two elements , grab both.
            if len(sal_and_pos) == 2:
                salary = sal_and_pos[0].text
                position_status = sal_and_pos[1].text.replace(u'\xa0', '')
                # Hyphen only exists when there are two elements.
                pattern = '-.*?'
                position_status = re.sub(pattern, '', position_status, count=1).split(',')
            # Otherwise, if the single element contains digits, assign to salary.
            elif bool(re.search(r'\d', sal_and_pos[0].text)):
                salary = sal_and_pos[0].text
                position_status = None
            # If no digits, assign to position status instead.
            else:
                salary = None

                position_status = sal_and_pos[0].text.replace(u'\xa0', '').split(',')
        # When salary & position doesn't exist
        except AttributeError:
            salary = None
            position_status = None

        # Get company logo
        try:
            company_logo = html.find('img', class_='jobsearch-CompanyAvatar-image')['src']
        # Company doesn't have logo uploaded
        except TypeError:
            company_logo = None

        # Grab date posted
        try:
            date_posted = job_container.find('div', class_='jobsearch-JobMetadataFooter').text
            temp = re.findall(r'\d+', date_posted)  # Check if number exists

            # If number doesn't exist, job is posted today.
            date_posted = datetime.strftime(datetime.today(), '%d-%m-%Y') if not temp else \
                datetime.strftime(datetime.today() - timedelta(days=int(temp[0])), '%d-%m-%Y')
        except AttributeError:
            date_posted = None

        # Grab job description
        try:
            job_description = job_container.find('div', id='jobDescriptionText').text
        except AttributeError:
            job_description = None

        print(company)

        return {'Company': company,
                'Logo': company_logo,
                'Location': location,
                'Title': job_title,
                'Salary': salary,
                'Position': position_status,
                'Date_posted': date_posted,
                'Job_desc': job_description,
                'Link': link}

    def job_links(self, num_jobs):  # num jobs = 25
        """
        Method used to generate the individual job links
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


class SeekScraper(Scraper):
    def __init__(self):
        super().__init__()


class LinkedinScraper(Scraper):
    def __init__(self):
        super().__init__()