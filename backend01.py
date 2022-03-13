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
    def __init__(self, location: str, title: str, time_type: str, minimum_experience: int,
                 df: pd.DataFrame = None, filter_df: pd.DataFrame = None):

        self.filtered_df = filter_df
        self.output_df = df
        self.input_location = location
        self.input_title = title
        self.input_type = time_type
        self.input_experience = minimum_experience

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
        current_results = 0  # For progress tracking

        # If the number of total results is greater than the max_results desired, calculate pg loops using max_results
        if max_results < int(total_results):
            total_results = max_results
            pg_loops = range(0, int(int(total_results) / 10))
        else:
            pg_loops = range(0, int(int(total_results) / 10))

        # Visual stuff
        # print('Search Term:', self.input_title.upper(), self.input_location.upper(), self.input_type.upper())
        # print('Total Results:', total_results)
        # print('Loops:', pg_loops)
        # print('Page | Results Scraped')
        # print('----------------------')

        current_pg = 0  # Set initial start result in loop to zero
        result_lst = []  # Set empty result list (to be converted to df)

        for pg in pg_loops:
            # print('|', pg, '         ', current_pg, '     |')

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

                progress = int(current_results / int(total_results) * 100)

                if progress < 100:
                    print(str(progress) + '%')  # Current Progress
                elif progress >= 100:
                    print('100%. Wrapping up..')  # print 100 if current progress above 100

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

                current_results += 1

            current_pg += 10

        # Create pandas DataFrame and drop duplicates
        jobs_df = pd.DataFrame(result_lst)
        jobs_df = jobs_df.drop_duplicates(subset='url', keep='first')

        # Return output_df as self parameter
        self.output_df = jobs_df

        return self

    def filter(self):

        # Initialize regexes to search through in text and join regex patterns into one search critieria
        regexes = [
            # r"{}(\d)?(\+)?\s+year(s)\s+?(([^\s]+)\s+){{0,9}}experience" resolve issue of 10+ experience when 1 is min

            r"{}(\+)?\s+year(s)\s+?(([^\s]+)\s+){{0,9}}experience".format(str(self.input_experience)),
            r"{}(\+)?\s+year(s)\s+.Required.".format(str(self.input_experience)),
            r"{}(\+)?\s+year(s)\s+.Preferred.".format(str(self.input_experience)),

            r"{}(\s+)?(\-)(\s+)?\d(\d)?\s+year(s)\s+?(([^\s]+)\s+){{0,9}}experience".format(
                str(self.input_experience)),
            r"{}(\s+)?(\-)(\s+)?\d(\d)?\s+year(s)\s+.Required.".format(str(self.input_experience)),
            r"{}(\s+)?(\-)(\s+)?\d(\d)?\s+year(s)\s+.Preferred.".format(str(self.input_experience))
        ]

        combined = "(" + ")|(".join(regexes) + ")"

        # Only return df rows where work experience criteria is met
        self.output_df['yrs_req_met'] = self.output_df['job_desc'].str.contains(combined)
        self.filtered_df = self.output_df.loc[self.output_df['yrs_req_met'] == True]

        return self

    def export(self, dataset: str):
        # Export filtered df if input is 'f' or all jobs if input is 'a'
        if dataset.lower() == 'f':
            self.filtered_df.to_csv('filtered-job-results\\filtered-jobs.csv')

        elif dataset.lower() == 'a':
            self.output_df.to_csv('all-job-results\\all-jobs.csv')

        else:
            raise ValueError('Please enter one from the list: [F, A]')

    # def similar(self, basis: str):  # filter jobs, remove titles (director, mgr.) and return keywords in titles
    #     if basis == 't':
    #         print('Finding similar titles.')
    #         all_jobs = self.output_df['job_title']
    #         filtered_jobs = self.filtered_df['job_title']

    # 1. Get common text occurences from filtered posting that relate to skills and responsibilities
    # 2. Aggregate common text into a list ['analytical', 'Excel', 'strategic recommendations']
    # 3. Compare this list to the overall job posting and assign compatability score to each posting
    # 4. If comp. score is greater than 90%, return the title without the level in it (ex. strategy manager)
    # becomes strategy

    # years = self.years_experience

    #
    # elif basis == 'l':
    #     print('Finding similar locations.')
    #     location = self.input_location

    # def compare_compatability(self, compare_to: str or pd.DataFrame, compare_from: str or pd.DataFrame):
    # if type(compare_from) == str:
    # same concept here, use the filtered shortlist to compare jobs against a new search term

    # Using this space for additional features (Coming soon)
    #       - Directly upcoming features include option to find similar job titles and similar locations
    #    def similar titles; input 3
    # compatibilty score = (text similarity) / (years required / years held)


if __name__ == '__main__':
    js = JobSearch(title='strategy consultant', location='Washington DC', time_type='fulltime', minimum_experience=1)
    results = js.jobs(max_results=10)
    filtered = results.filter()
    results.export(dataset='a')
    filtered.export(dataset='f')

    print('Search complete')
