#!/usr/bin/env python

"""
The Razors retrieve data from TriMet and return a list of arrival times.

This module contains the 'razors'.  Each razor pulls the data from one
type of TriMet vehicle and spits out a list of arrival times for a single
StopID.
"""

import datetime
import requests
import copy

BASE_URL = r"http://developer.trimet.org/ws/V1/arrivals"
DATE_FORMAT = r"%Y-%m-%dT%H:%M:%S"
BASE_PARAMS = dict(
    json='true',
    appID='80CC2DA961B59703E3ADDA3B2'
)


def parse_date(date_str):
    """
    Parse a TriMet timestamp string and return a datetime object.

    :param str date_str: A TriMet timestamp string.
    """

    # What the hell, Wil?  Why... ?
    if len(date_str) == 28:
        date_str = date_str.split('.')[0]

    date_time = datetime.datetime.strptime(date_str, DATE_FORMAT)

    return date_time


def diff_datetime_in_seconds(a_time, b_time):
    """
    Take two datetime objects and return the difference between them in seconds.

    Returns a float produced by (a_time - b_time).  If a_time is later than b_time,
    the return value will be positive.

    :param datetime a_time: The first datetime object.
    :param datetime b_time: The second datetime object.
    """
    delta = a_time - b_time

    return delta.total_seconds()


def dt_now():
    """A convenience function to improve readability."""
    return datetime.datetime.now()


class Razor(object):
    """
    This is the base class for the Razors.

    It accepts either a list/tuple of integer TriMet locIDs, or a single integer
    locID for the loc_ids parameter.  The timeout is the minimum requery delay.

    :param int loc_ids: The TriMet stop ID number that this Razor will query.
    :param list loc_ids: The TriMet stop ID numbers that this Razor will query.
    :param int timeout: Minimum number of seconds between queries. (default=10)
    """

    def __init__(self, loc_ids, timeout=10):
        self.timeout = timeout

        if not isinstance(loc_ids,(int,tuple,list)):
            raise Exception("I need an int, tuple of ints, or list of ints to create "
                            "a Razor.")

        if isinstance(loc_ids, int):
            loc_ids = [loc_ids]

        if len(loc_ids) > 10:
            raise Exception("TriMet won't return more than ten locations at once.")

        self.loc_ids = loc_ids
        self.params = copy.deepcopy(BASE_PARAMS)

        self.params['locIDs'] = ','.join([str(x) for x in loc_ids])

    def query_arrivals(self, override_timeout=False):
        """
        Query the TriMet server for arrival times.

        :param bool override_timeout: Ignore the timeout that normally prevents
                                      too-frequent requests of the TriMet server.
        """

        # You're requesting too frequently!  No query for you!
        try:
            if self.time_since_last_query() < self.timeout and not override_timeout:
                return False
        except AttributeError:
            pass

        # Perform the request and store the result.
        self._latest_response = requests.get(url=BASE_URL, params=self.params).json()
        self._latest_query_datetime = parse_date(
            self._latest_response['resultSet']['queryTime']
        )

        return True

    def time_since_last_query(self):
        return diff_datetime_in_seconds(self._latest_query_datetime, dt_now())

    def next_up(self):
        """
        Return a list of (seconds_until_arrival, fullSign) tuples for upcoming arrivals.
        """
        arrivals = self._latest_response['resultSet']['arrival']

        next_arrivals = list()

        for arr in arrivals:
            if arr['status'] == u'estimated':
                estimated_date_time = parse_date(arr['estimated'])
                til = diff_datetime_in_seconds(estimated_date_time, dt_now())
                next_arrivals.append((til,arr['fullSign']))

        if len(next_arrivals) == 0:
            next_arrivals = None
        return next_arrivals


class StreetcarRazor(Razor):
    """
    This is the streetcar-specific razor.
    """
    def __init__(self, loc_ids, timeout=10):
        super(StreetcarRazor, self).__init__(loc_ids, timeout)

        self.params['streetcar'] = 'true'


def main():
    """
    For test execution.
    """
    tmr = StreetcarRazor(10760)
    tmr.query_arrivals()
    tils = tmr.next_up()
    print tils


if __name__ == "__main__":
    main()
