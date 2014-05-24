#!/usr/bin/env python

"""
"""

import requests
import datetime
# import sys
# from PyQt4 import QtGui


class StreetcarRazor:
    """
    """

    def __init__(self):
        self.baseURL = "http://developer.trimet.org/ws/V1/arrivals"

        self.dateFormat = '%Y-%m-%dT%H:%M:%S'

        self.baseParams = dict(
            json='true',
            appID='80CC2DA961B59703E3ADDA3B2',
            streetcar='true'
            )

    def getArrivals(self,locIDs):
        params = self.baseParams.copy()

        if isinstance(locIDs, list) or isinstance(locIDs, tuple):
            if len(locIDs) > 10:
                raise Exception("Can't ask for more than ten locations at once.")
            params['locIDs'] = ','.join(locIDs)
        else:
            params['locIDs'] = locIDs

        self.latestResponse = requests.get(url=self.baseURL, params=params).json()
        self.latestMyQTime = datetime.datetime.now()
        self.latestServerQTime = self.parseDate(self.latestResponse['resultSet']['queryTime'])
        self.serverBehindMeBy = self.latestMyQTime - self.latestServerQTime

    def parseDate(self,dateStr,format=None):
        if format is None:
            format = self.dateFormat

        if len(dateStr) == 28:
            dateStr = dateStr.split('.')[0]

        dateTime = datetime.datetime.strptime(dateStr, format)

        return dateTime

    def diffDatetimeSeconds(self, aTime, bTime):
        diff = aTime - bTime

        return diff.total_seconds()

    def timeSinceLastQuery(self):
        return self.diffDatetimeSeconds(self.latestServerQTime, self.serverNow())

    def serverNow(self):
        return datetime.datetime.now() - self.serverBehindMeBy


    def nextUp(self, onlyReturnResultsContaining=None):
        arrivals = self.latestResponse['resultSet']['arrival']

        nextArrivalsInSeconds = list()

        for arr in arrivals:
            if (onlyReturnResultsContaining == None or
                        onlyReturnResultsContaining in arr['fullSign']):
                if arr['status'] == u'estimated':
                    estimatedDatetime = self.parseDate(arr['estimated'])
                    til = self.diffDatetimeSeconds(estimatedDatetime, self.serverNow())
                    nextArrivalsInSeconds.append(til)

        if len(nextArrivalsInSeconds) == 0:
            nextArrivalsInSeconds = None
        return nextArrivalsInSeconds

def main():
    tmr = StreetcarRazor()
    tmr.getArrivals(10760)
    tils = tmr.nextUp(onlyReturnResultsContaining='NS')
    print tils

    # app = QtGui.QApplication(sys.argv)
    # trayIcon = QtGui.QSystemTrayIcon(QtGui.QIcon("Bomb.xpm"), app)
    # menu = QtGui.QMenu()
    # exitAction = QtGui.QAction(QtGui.QIcon.fromTheme('exit'), '&Exit', app)
    # exitAction.triggered.connect(app.quit)
    # for til in tils:
    #     titem = menu.addAction(str(til))
    #     titem.triggered.connect(app.quit)
    # menu.addAction(exitAction)
    # trayIcon.setContextMenu(menu)
    # trayIcon.show()
    # sys.exit(app.exec_())

if __name__ == "__main__":
    main()
