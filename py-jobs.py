import time
import random
import re

from bs4 import BeautifulSoup
from msedge.selenium_tools import EdgeOptions
from msedge.selenium_tools import Edge

import pandas as pd

options = EdgeOptions()
options.use_chromium = True
options.add_argument("headless")  # Run as headless browser to avoid pop-ups on screen
options.add_argument("disable-gpu")  # Disable graphical processing unit processing acceleration
browser = Edge("msedgedriver.exe", options=options)  # Configure Edge driver


class JobSearch:
    def __init__(self, location: str, title: str, time_type: str,
                 all_df: pd.DataFrame = None, filter_df: pd.DataFrame = None):

        self.filtered_df = filter_df
        self.output_df = all_df
        self.input_location = location
        self.input_title = title
        self.input_type = time_type

        # Allow certain inputs for time_type argument and raise value error if none are met
        if time_type not in ['fulltime', 'parttime', 'temporary']:
            raise ValueError('Please enter one from the list: [fulltime, parttime, temporary]')

    def jobs(self, max_results: int = 999999):

        # Create search URL for first page (used to scrape total pages in search query)
        start_url = 'https://www.indeed.com/jobs?q={}&l={}&jt={}&start=0' \
            .format(self.input_title.replace(' ', r'%20'), self.input_location.replace(' ', r'%20'), self.input_type)

        time.sleep(random.randint(5, 8))

        browser.get(start_url)
        soup = BeautifulSoup(browser.page_source, 'html.parser')

        # Parse HTML and find the total amount of results in the search query
        pg_count = soup.find('div', {'id': 'searchCountPages'}).getText().strip()
        total_results = re.search(r'of (.*) jobs', pg_count).group(1)
        total_results = total_results.replace(',', '')

        # If the number of total results is greater than the max_results desired, calculate pg loops using max_results
        if max_results < int(total_results):
            pg_loops = range(0, int(max_results / 10))
        else:
            pg_loops = range(0, int(int(total_results) / 10))

        # Visual stuff
        print('Search Term:', self.input_title.upper(), self.input_location.upper(), self.input_type.upper())
        print('Total Results:', total_results)
        print('Loops:', pg_loops)
        print('Page | Results Scraped')
        print('----------------------')

        current_pg = 0  # Set initial start result in loop to zero
        result_lst = []  # Set empty result list (to be converted to df)

        for pg in pg_loops:
            print('|', pg, '         ', current_pg, '     |')

            # Create URL using current_pg to move across different pages in the site
            paginated_url = 'https://www.indeed.com/jobs?q={}&l={}&jt={}&start={}' \
                .format(self.input_title.replace(' ', r'%20'),
                        self.input_location.replace(' ', r'%20'),
                        self.input_type, str(current_pg))

            time.sleep(random.randint(5, 8))

            browser.get(paginated_url)
            results_soup = BeautifulSoup(browser.page_source, 'html.parser')

            # Parse data and return all jobs that are non-ad jobs (i.e., return jobs relevant to search term only)
            results_data = results_soup.find_all('a', href=True)
            data_to_parse = [data for data in results_data if data.has_attr('data-jk') and 'pagead' not in data['href']]

            # Further parse and seperate relevant information pertaining to job and add those features to
            # a dict (consider these rows) and append each job to the final result_lst
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

                # Join all line breaks in the job description
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

        # Create pandas DataFrame and drop duplicates
        jobs_df = pd.DataFrame(result_lst)
        jobs_df = jobs_df.drop_duplicates(subset='url', keep='first')

        # Return output_df as self parameter
        self.output_df = jobs_df

        return self

    def filter(self, minimum_experience: int):

        # Initialize regexes to search through in text and join regex patterns into one search critieria
        regexes = [

            r"{}(\+)?\s+year(s)\s+?(([^\s]+)\s+){{0,9}}experience".format(str(minimum_experience)),
            r"{}(\+)?\s+year(s)\s+.Required.".format(str(minimum_experience)),
            r"{}(\+)?\s+year(s)\s+.Preferred.".format(str(minimum_experience)),

            r"{}(\s+)?(\-)(\s+)?\d(\d)?\s+year(s)\s+?(([^\s]+)\s+){{0,9}}experience".format(
                str(minimum_experience)),
            r"{}(\s+)?(\-)(\s+)?\d(\d)?\s+year(s)\s+.Required.".format(str(minimum_experience)),
            r"{}(\s+)?(\-)(\s+)?\d(\d)?\s+year(s)\s+.Preferred.".format(str(minimum_experience))
        ]

        combined = "(" + ")|(".join(regexes) + ")"

        # Only return df rows where work experience criteria is met
        self.output_df['yrs_req_met'] = self.output_df['job_desc'].str.contains(combined)
        self.filtered_df = self.output_df.loc[self.output_df['yrs_req_met'] == True]

        return self

    def export(self, dataset: str):
        # Export filtered df if input is 'f' or all jobs if input is 'a'
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

    js = JobSearch(title='software engineer', location='san francisco ca', time_type='fulltime')
    results = js.jobs(max_results=200)
    filtered = results.filter(minimum_experience=1)
    results.export(dataset='a')
    filtered.export(dataset='f')

    print('Process Ended.')
