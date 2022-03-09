import re

from bs4 import BeautifulSoup
from msedge.selenium_tools import EdgeOptions
from msedge.selenium_tools import Edge

import pandas as pd
import time
import random

options = EdgeOptions()
options.use_chromium = True
options.add_argument("headless")
options.add_argument("disable-gpu")
browser = Edge("msedgedriver.exe", options=options)


class JobSearch:
    def __init__(self, location: str, title: str, time_type: str,
                 df: pd.DataFrame = None, filter_df: pd.DataFrame = None):

        self.filtered_df = filter_df
        self.output_df = df
        self.input_location = location
        self.input_title = title
        self.input_type = time_type

        if time_type not in ['fulltime', 'parttime', 'temporary']:
            raise ValueError('Please enter one from the list: [fulltime, parttime, temporary]')

    def jobs(self):

        start_url = 'https://www.indeed.com/jobs?q={}&l={}&jt={}&start=0' \
            .format(self.input_title.replace(' ', r'%20'), self.input_location.replace(' ', r'%20'), self.input_type)

        print(start_url)

        time.sleep(random.randint(5, 8))

        browser.get(start_url)
        soup = BeautifulSoup(browser.page_source, 'html.parser')

        pg_count = soup.find('div', {'id': 'searchCountPages'}).getText().strip()
        total_results = re.search(r'of (.*) jobs', pg_count).group(1)
        pg_loops = range(0, int(int(total_results) / 10) - 52)

        print('Pages:', pg_loops)
        print('Page | Results Scraped')
        print('----------------------')

        current_pg = 0

        result_lst = []

        for pg in pg_loops:
            print('|', pg, '         ', current_pg, '     |')
            paginated_url = 'https://www.indeed.com/jobs?q={}&l={}&jt={}&start={}' \
                .format(self.input_title.replace(' ', r'%20'),
                        self.input_location.replace(' ', r'%20'),
                        self.input_type, str(current_pg))

            time.sleep(random.randint(5, 8))

            browser.get(paginated_url)
            results_soup = BeautifulSoup(browser.page_source, 'html.parser')

            results_data = results_soup.find_all('a', href=True)
            data_to_parse = [data for data in results_data if data.has_attr('data-jk') and 'pagead' not in data['href']]

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
                result_dict['job_type'] = self.input_type
                result_dict['job_salary'] = job_salary
                result_dict['job_desc'] = job_desc
                result_dict['url'] = sub_url

                result_lst.append(result_dict)

            current_pg += 10

        jobs_df = pd.DataFrame(result_lst)
        jobs_df = jobs_df.drop_duplicates(subset='url', keep='first')

        self.output_df = jobs_df

        return self

    def filter(self, minimum_experience: int):

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

        self.output_df['yrs_req_met'] = self.output_df['job_desc'].str.contains(combined)
        self.filtered_df = self.output_df.loc[self.output_df['yrs_req_met'] == True]

        return self

    def export(self, dataset: str):
        if dataset.lower() == 'f':
            self.filtered_df.to_csv('filtered-jobs.csv')

        elif dataset.lower() == 'a':
            self.output_df.to_csv('all-jobs.csv')

        else:
            raise ValueError('Please enter one from the list: [F, A]')

    # Using this space for additional features (Coming soon)
    #       - Directly upcoming features include option to find similar job titles and similar locations


if __name__ == '__main__':

    print('Process Starting.')
    
    js = JobSearch(title='brand analyst', location='San Francisco CA', time_type='fulltime')
    results = js.jobs()
    filtered = results.filter(minimum_experience=1)
    results.export(dataset='a')
    filtered.export(dataset='f')

    print('Process Ended.')