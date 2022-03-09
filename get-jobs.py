"""
What is it: A Python job scraper differentiated through application of strict "experience level" filtering to avoid:
    1) Time wasting
    2) Increased stress and/or discouragement
    3) Missed opportunities

NOTE: This is an advanced search built to target certain phrases in job descriptions.
In almost all cases, the number of jobs returned will be less than what you would find on Indeed.com.
This means this bot could easily miss a job that you qualify for because it failed to return a keyword match.
Thus, it is recommended that you do your own due diligence and apply other tools and methods in addition to this one.

---------------------------------
===== Current v1 Features =====
---------------------------------

* Use Indeed.com to scrape all relevant jobs filtered by 1) Title 2) Location 3) Job Type (Full-time, Remote) (X)

* Jobs scraped will return 1) Company 2) Job Title 3) Job Location 4) Estimated Salary 5) Actual Required Experience
                           6) Full job description in the form of a CSV file (X)

* Options to export jobs in form of queried dataframe output (as .csv file) saved to local directory or emailed

* (Non-)analytic keyword search and match against a list of given skills using regex matching and cosine similarity
against whole document

---------------------------------
===== Intended v2 Additions =====
---------------------------------
* Input current skills to match relevant jobs

* Option to find similar jobs using textual analysis on job titles and descriptions

* Analytics will be performed to find similar job titles with similar minimum requirements
  from an experience perspective

"""
import re

from bs4 import BeautifulSoup
from msedge.selenium_tools import EdgeOptions
from msedge.selenium_tools import Edge

import pandas as pd
from math import floor
import time
import random

options = EdgeOptions()
options.use_chromium = True
options.add_argument("headless")
options.add_argument("disable-gpu")
browser = Edge("msedgedriver.exe", options=options)


class JobSearch:
    #def __init__(self):
        #self.jobs_df = pd.DataFrame()

    def get_jobs(self, title: str, location: str, job_type='fulltime'):

        start_url = 'https://www.indeed.com/jobs?q={}&l={}&jt={}&start=0' \
            .format(title.replace(' ', r'%20'), location.replace(' ', r'%20'), job_type)

        time.sleep(random.randint(5, 8))

        browser.get(start_url)
        soup = BeautifulSoup(browser.page_source, 'html.parser')

        pg_count = soup.find('div', {'id': 'searchCountPages'}).getText().strip()
        final_pg = re.search(r'of (.*) jobs', pg_count).group(1)
        pg_loops = range(0, int(int(final_pg)/10))
        print('Pages:', pg_loops)
        print('Page | Results Scraped')
        print('----------------------')

        current_pg = 0

        result_lst = []

        for pg in pg_loops:
            print('| ', pg, '           ', current_pg, '      |')
            paginated_url = 'https://www.indeed.com/jobs?q={}&l={}&jt={}&start={}' \
                .format(title.replace(' ', r'%20'), location.replace(' ', r'%20'), job_type, str(current_pg))

            time.sleep(random.randint(5, 8))

            browser.get(paginated_url)
            job_soup = BeautifulSoup(browser.page_source, 'html.parser')

            job_data = job_soup.find_all('a', href=True)
            data_to_parse = [data for data in job_data if data.has_attr('data-jk') and 'pagead' not in data['href']]

            for data in data_to_parse:

                result_dict = {}

                try:
                    job_title = data.find("h2", {"class": 'jobTitle jobTitle-newJob'}).getText()
                except AttributeError:
                    job_title = data.find("h2", {"class": 'jobTitle'}).getText()

                try:
                    job_salary = data.find("div", {"class": 'metadata salary-snippet-container'}).getText()
                except AttributeError:
                    job_salary = 'Nan'

                job_company = data.find("span", {"class": 'companyName'}).getText()
                job_location = data.find("div", {"class": 'companyLocation'}).getText()

                sub_url = 'https://www.indeed.com' + data['href']

                text_lst = []

                time.sleep(random.randint(5, 8))

                browser.get(sub_url)
                sub_soup = BeautifulSoup(browser.page_source, 'html.parser')
                job_data = sub_soup.find('div', {'id': 'jobDescriptionText', 'class': ['jobsearch-jobDescriptionText']})

                if job_data is not None:
                    text = job_data.getText()
                    text_lst.append(text)

                job_desc = ''.join(text_lst)

                result_dict['job_title'] = job_title
                result_dict['job_company'] = job_company
                result_dict['job_location'] = job_location
                result_dict['job_type'] = job_type
                result_dict['job_salary'] = job_salary
                result_dict['job_desc'] = job_desc
                result_dict['url'] = sub_url

                result_lst.append(result_dict)

            current_pg += 10

        jobs_df = pd.DataFrame(result_lst)

        return jobs_df

    def filter(self, df, minimum_experience: int):

        regexes = [
            # r"{}(\d)?(\+)?\s+year(s)\s+?(([^\s]+)\s+){{0,9}}experience" resolve issue of 10+ experience when 1 is min

            r"{}(\+)?\s+year(s)\s+?(([^\s]+)\s+){{0,9}}experience".format(str(minimum_experience)),
            r"{}(\+)?\s+year(s)\s+.Required.".format(str(minimum_experience)),
            r"{}(\+)?\s+year(s)\s+.Preferred.".format(str(minimum_experience)),

            r"{}(\s+)?(\-)(\s+)?\d(\d)?\s+year(s)\s+?(([^\s]+)\s+){{0,9}}experience".format(
                str(minimum_experience)),
            r"{}(\s+)?(\-)(\s+)?\d(\d)?\s+year(s)\s+.Required.".format(str(minimum_experience)),
            r"{}(\s+)?(\-)(\s+)?\d(\d)?\s+year(s)\s+.Preferred.".format(str(minimum_experience))
        ]

        combined = "(" + ")|(".join(regexes) + ")"

        df['yrs_req_met'] = df['job_desc'].str.contains(combined)
        df = df.loc[df['yrs_req_met'] == True]

        return df

    #def similar

    def export(self, df, email=False):
        df.to_csv('jobs.csv')

        if not email:
            print('Not Emailed.')


if __name__ == '__main__':
    js = JobSearch()
    print('Process Started')
    jobs = js.get_jobs('brand analyst', 'San Francisco, CA', 'fulltime')
    filtered_jobs = js.filter(df=jobs, minimum_experience=1)
    js.export(filtered_jobs)

    print('Process Complete')
