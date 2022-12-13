from datetime import date

PYTHON_RELEASE_DATES = {version: date.fromisoformat(d) for version, d in {
    "2.0": "2000-10-16",
    "2.1": "2001-04-15",
    "2.2": "2001-12-21",
    "2.3": "2003-06-29",
    "2.4": "2004-11-30",
    "2.5": "2006-09-19",
    "2.6": "2008-10-01",
    "2.7": "2010-07-03",
    "3.0": "2008-12-03",
    "3.1": "2009-06-27",
    "3.2": "2011-02-20",
    "3.3": "2012-09-29",
    "3.4": "2014-03-16",
    "3.5": "2015-09-13",
    "3.6": "2016-12-23",
    "3.7": "2018-06-27",
    "3.8": "2019-10-14",
    "3.9": "2020-10-05",
    "3.10": "2021-10-04",
    "3.11": "2022-10-24"
}.items()}


def possible_versions(commit_date: date) -> list[tuple[int, int]]:
    return [version for version, v_date in PYTHON_RELEASE_DATES.items() if v_date <= commit_date]
