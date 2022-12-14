"""
####################################################################################################

This module extracts race data (speed[m/s] and stroke[1/min]) for each country per race and writes them to a json file.
Those files for which the extraction process fails, the corresponding URLs are written to a failed_requests.json file.

Basic stats:
* For the 1000 competition IDs provided by the API, there are approximately 11.700 race data pdfs.
* Processing time per pdf: approx. 1.2 - 1.8s
* Time to process 12k pdfs: approx. 4 hours

####################################################################################################
"""

import camelot  # on Mac via 'pip install camelot-py[cv]'
from tqdm import tqdm
import itertools
import pandas as pd
from typing import Union

from utils_general import write_to_json
from api import get_competition_ids, get_pdf_urls
from utils_pdf import (handle_table_partitions, get_data_loc, print_stats,
                       clean_df, get_string_loc, check_speed_stroke, reset_axis, clean_str)
import logging

logger = logging.getLogger(__name__)

# constants
COMPETITION_LIMIT = 1000  # max limit of world rowing API is 1000 in total --> not relevant for per year extraction
EVERY_NTH_DOCUMENT = 7  # testwise extraction --> only consider every nth document
START_YEAR = 2010
END_YEAR = 2022
# special codes for the country line, which could affect the detection --> list contains values that are excluded
SPECIAL_NAMES_FOR_COUNTRY_ROW = ["NPC", "NOC"]


def read_race_data(df: pd.DataFrame) -> Union[dict, None]:
    """
    Extracts countries, ranks, speeds and strokes from final dataframe and return json structure.
    """
    if df.empty:
        return
    df = clean_df(df)
    # handle top part with countries and ranks: get index of country code row, check if ranks are present
    country_idx = next(iter(get_string_loc(df, country=True)["cntry"]["row"]), None)
    rank_found = bool(get_string_loc(df, rank=True, column=0)["rank"]["row"])
    # create df for table head, and reset row axis, if ranks present include ranks row else only take country row
    if country_idx is None:
        logger.warning("No country found – ignore file...")
        return
    table_head_df = reset_axis(df.iloc[country_idx:country_idx + (2 if rank_found else 1)], axes=[0])

    # extract country codes
    country_data = table_head_df.iloc[0:1, 1:].values.flatten().tolist()
    country_list = [x.split('\n') for x in country_data if x and x not in SPECIAL_NAMES_FOR_COUNTRY_ROW]
    countries = list(itertools.chain(*country_list))
    countries = clean_str(countries, style="country")

    # handle ranks data; if ranks are found they are present in the row below the county code
    ranks = None
    if rank_found:
        ranks_data = next(iter(table_head_df.iloc[1:2, 1:].values), None)
        ranks = [rank for rank in ranks_data if rank]
        # assumption for each country a rank is provided
        if ranks and len(ranks) == len(countries):
            ranks = ranks
        # if num of ranks and countries not equal, mapping cannot be guaranteed --> return None for all
        else:
            ranks = [None] * len(countries)

    # Handle actual race data part
    data_range = get_data_loc(df)
    data_df = df.iloc[data_range[0]:data_range[1] + 1]

    # get distance values
    dist = clean_str(data_df.iloc[:, 0:2].values, style="dist")

    # map race data and ranks to countries
    boat_data, offset = {}, 0
    for index, country in enumerate(countries):
        # Idea here: As speed and stroke data occur in pairs we can shift 2-column window over dataframe
        # to read speed-stroke pairs per country. Offset is added to correct column alignment.
        speed_data = data_df.iloc[:, (index + 1) + offset: (index + 2) + offset]
        stroke_data = data_df.iloc[:, (index + 2) + offset: (index + 3) + offset]
        # write to boat data dict that represents one boat in a race
        boat_data[index] = {
            "country": country,
            "rank": ranks[index] if ranks else None,
            "data": {
                "dist [m]": dist,
                # info for speed upper bound: highest occurring speed value in dataset was 9.8
                "speed [m/s]": check_speed_stroke(speed_data, lb=0.01, ub=9.9),
                "stroke": check_speed_stroke(stroke_data, lb=10., ub=100.)
            }
        }
        offset += 1
    return boat_data


def exclude_empty_files(data: dict, limit: int = 5) -> dict:
    """
    Excludes files that do not contain a specified limit of data values.
    Background: If there are only very few values, e.g. 2-3 per country, mapping the values
    to a certain column tends to be inaccurate.
    """
    if data:
        num_of_speed_values = [len(v["data"]["speed [m/s]"]) for v in data.values() if "data" in v]
        num_of_stroke_values = [len(v["data"]["stroke"]) for v in data.values() if "data" in v]
        more_than_limit_speeds = all(list(map(lambda x: x >= limit, num_of_speed_values)))
        more_than_limit_strokes = all(list(map(lambda x: x >= limit, num_of_stroke_values)))

        if more_than_limit_speeds and more_than_limit_strokes:
            return data
        else:
            logger.warning(f" Found less than {limit} GPS data values per country. Ignore file.")
            return {}
    return {}


def extract_table_data_from_pdf(urls: list) -> tuple[list, list]:
    """
    Extracts data from given pdf urls using camelot-py
    -----------------------
    Parameters:
    * urls:     list containing all urls for pdf files
    -----------------------
    Returns: tuple
    * list with json objects (final structure needs to be discussed) for each team per race
    * list containing the urls of all failed requests
    """
    data, failed_reqs, errors, empty_files = [], [], 0, 0

    for url in tqdm(urls):
        try:
            # read data via camelot
            tables = camelot.read_pdf(url, flavor="stream", pages="all")
            # handle data that is spread across multiple pages, linebreaks and empty columns
            df = handle_table_partitions(tables=tables, results=False)
            # extract relevant data and return dict
            data_dict = read_race_data(df=df)
            # exclude files that are below a specific limit of relevant data values
            race_data_dict = exclude_empty_files(data=data_dict, limit=5)

            if race_data_dict:
                race_data_dict["url"] = url
                data.append(race_data_dict)
                logging.info(f"Extract of {url.split('/').pop()} successful.")
            else:
                empty_files += 1
                logging.warning(f"Empty file found: {url.split('/').pop()}.")

        except Exception as e:
            errors += 1
            failed_reqs.append(url)
            logging.error(f"\nError at {url}:\n{e}.\nErrors so far: {errors}.")

    # create extraction statistics
    total = len(pdf_urls) - empty_files
    extraction_rate = "{:.2f}".format(100-((errors/total if total else 0)*100))
    print_stats(total=total, errors=errors, empties=empty_files, rate=extraction_rate)

    return data, failed_reqs


# extract data per year and write data and failed requests to respective json files
final_extracted_data, final_failed_requests = [], []

for year in range(START_YEAR, END_YEAR):
    logger.info(f"Start extraction for year: {year}")
    # get competition ids for current year
    competition_ids = get_competition_ids(years=year)
    # fetch pdf urls for given competition ids
    pdf_urls = get_pdf_urls(comp_ids=competition_ids, comp_limit=COMPETITION_LIMIT, results=False)[::EVERY_NTH_DOCUMENT]
    # extract race data and get list of failed requests
    race_data, failed_requests = extract_table_data_from_pdf(urls=pdf_urls)
    # append to final list
    final_extracted_data.append(race_data)
    final_failed_requests.append(failed_requests)

write_to_json(data=final_extracted_data, filename="race_data")
write_to_json(data=final_failed_requests, filename="race_data_failed")

'''
# Use this to test selected files
pdf_urls = [
    "https://d3fpn4c9813ycf.cloudfront.net/pdfDocuments/WCH_2017/WCH_2017_ROWXCOXED4--PR3-------PREL000100--_MGPSX7872.pdf"
]
race_data, failed_requests = extract_table_data_from_pdf(urls=pdf_urls)

write_to_json(data=race_data, filename="race_data")
write_to_json(data=failed_requests, filename="race_data_failed")
'''