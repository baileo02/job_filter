import json

# Data loading



def job_filter():
    """
    Loads json object given in a specific format and filters the job by its description.

    Keywords used:
        kw_visa -> Positively connotated words for working visa.
        temp_visa -> Neutral keywords that mention working/temporary visa.
    filtered_jobs: Jobs are stored in a nested dictionary, separated in a list.

    :return:
    """

    with open('../../job_data.json', 'r') as rf:
        data = json.load(rf)

    kw_visa = ['valid temporary visa', 'valid work permit', '482 ', 'valid visa', 'appropriate visa',
               'current visa', 'temporary visa holder may only occur if no suitable', 'working holiday visa']

    temp_visa = ['temporary visa', 'work visa', 'working visa']

    filtered_jobs = {'TR': [], 'PR': [], 'maybe': []}

    for job in data:
        if any(word in job['description'].lower() for word in kw_visa):
            filtered_jobs['TR'].append(job)
        elif any(word in job['description'].lower() for word in temp_visa):
            filtered_jobs['maybe'].append(job)
        else:
            filtered_jobs['PR'].append(job)

    with open('filteredJobs.json', 'w') as wf:
        json.dump(filtered_jobs, wf)


if __name__ == '__main__':
    job_filter()

    # with open('filteredJobs.json', 'r') as rf:
    #     data = json.load(rf)
    #
    # for d in data['TR']:
    #     print(d['link'])
