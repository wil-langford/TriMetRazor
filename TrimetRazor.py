#!/usr/bin/env python

import sys
from PyQt4 import QtGui, QtCore
import Razors

class RazorTableModel(QtCore.QAbstractTableModel):
    def __init__(self, stopID, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.stopID = stopID
        self.tmr = Razors.StreetcarRazor()
        self.updateTimes()

    def updateTimes(self):
        self.beginResetModel()
        self.tmr.getArrivals(self.stopID)
        self._times = self.tmr.nextUp(onlyReturnResultsContaining='NS')
        self.endResetModel()

    def emitAllDataChanged(self):
        if min(self._times)<0:
            self.updateTimes()
        else:
            self.dataChanged.emit(self.first(), self.last())

    def first(self):
        return self.createIndex(0,0)

    def last(self):
        return self.createIndex(self.rowCount()-1,2)

    def rowCount(self, QModelIndex_parent=None, *args, **kwargs):
        return len(self._times)

    def columnCount(self, *args, **kwargs):
        return 1

    def headerData(self, p_int, Qt_Orientation, int_role=None):
        # header = ['s', 'ms', 'bar']
        # if int_role == QtCore.Qt.DisplayRole:
        #     if Qt_Orientation == QtCore.Qt.Horizontal:
        #         return header[p_int]
        #     else:
        #         return str(p_int)
        return None

    def data(self, QModelIndex, int_role=None):
        self._times = self.tmr.nextUp(onlyReturnResultsContaining='NS')
        row = QModelIndex.row()
        col = QModelIndex.column()

        if col == 0:
            if int_role == QtCore.Qt.DisplayRole:
                min, sec = divmod(int(self._times[row]), 60)
                return "{}:{:02d}".format(min,sec)

            if int_role == QtCore.Qt.DecorationRole:
                timeleft = self._times[row]

                if timeleft > 10*60:
                    color = QtGui.QColor(0,150,0)
                elif timeleft < 6*60:
                    color = QtGui.QColor(150,0,0)
                else:
                    color = QtGui.QColor(200,200,0)

                pixmap = QtGui.QPixmap(self._times[row]//3, 10)
                pixmap.fill(color)
                return pixmap

class RazorListModel(QtCore.QAbstractListModel):
    def __init__(self, stopID, parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.stopID = stopID
        self.tmr = Razors.StreetcarRazor()
        self.updateTimes()

    def updateTimes(self):
        self.beginResetModel()
        self.tmr.getArrivals(self.stopID)
        self._times = self.tmr.nextUp(onlyReturnResultsContaining='NS')
        self.endResetModel()

    def emitAllDataChanged(self):
        if min(self._times)<0:
            self.updateTimes()
        else:
            self.dataChanged.emit(self.first(), self.last())

    def first(self):
        return self.createIndex(0,0)

    def last(self):
        return self.createIndex(self.rowCount()-1,0)

    def rowCount(self, QModelIndex_parent=None, *args, **kwargs):
        return len(self._times) + 1

    def headerData(self, p_int, Qt_Orientation, int_role=None):
        return ""

    def data(self, QModelIndex, int_role=None):
        self._times = self.tmr.nextUp(onlyReturnResultsContaining='NS')
        row = QModelIndex.row()

        if row < self.rowCount()-1:
            if int_role == QtCore.Qt.DisplayRole:
                min, sec = divmod(int(self._times[row]), 60)
                return "{}:{:02d}".format(min,sec)

            if int_role == QtCore.Qt.DecorationRole:
                timeleft = self._times[row]

                if timeleft > 10*60:
                    color = QtGui.QColor(0,150,0)
                elif timeleft < 6*60:
                    color = QtGui.QColor(150,0,0)
                else:
                    color = QtGui.QColor(200,200,0)

                pixmap = QtGui.QPixmap(self._times[row]//4, 10)
                pixmap.fill(color)
                return pixmap
        else:
            sec = -int(self.tmr.timeSinceLastQuery())

            if int_role == QtCore.Qt.DisplayRole:
                return "seconds since last query: {}".format(sec)

            if int_role == QtCore.Qt.DecorationRole:
                if sec < 60:
                    color = QtGui.QColor(0,150,0)
                elif sec > 70:
                    color = QtGui.QColor(150,0,0)
                else:
                    color = QtGui.QColor(200,200,0)

                pixmap = QtGui.QPixmap(50, 10)
                pixmap.fill(color)
                return pixmap


class RazorCentralWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(RazorCentralWidget, self).__init__()

        self.parent = parent

        self.cTimer = QtCore.QTimer()
        self.uiTimer = QtCore.QTimer()

        self.timesModel=RazorListModel(stopID=10760)

        self.secondsSinceLastQuery = self.timesModel.tmr.timeSinceLastQuery
        self.latestQueryTime = self.timesModel.tmr.latestMyQTime

        self.initUI()

    def initUI(self):

        grid = QtGui.QGridLayout()
        # grid.setSpacing(10)


        self.tableView = QtGui.QTableView(self)
        self.tableView.setModel(self.timesModel)
        self.tableView.clicked.connect(self.updateTimes)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

        grid.addWidget(self.tableView,1,0)

        self.cTimer.start(60*1000)
        self.cTimer.timeout.connect(self.updateTimes)

        self.uiTimer.start(1*1000)
        self.uiTimer.timeout.connect(self.parent.frequentUpdate)

        self.setLayout(grid)

    def updateTimes(self):
        self.timesModel.updateTimes()

    def redisplay(self):
        self.timesModel.emitAllDataChanged()


class RazorWindow(QtGui.QMainWindow):
    def __init__(self):
        super(RazorWindow, self).__init__()
        self.initUI(windowTitle='TriMet Razor')

    def initUI(self, windowTitle):
        exitAction = QtGui.QAction(QtGui.QIcon('/usr/share/icons/oxygen/128x128/actions/application-exit.png'), '&Exit',
                                   self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtGui.qApp.quit)
        self.addAction(exitAction)

        # self.statusBar().showMessage("Ready")

        # self.toolbar = self.addToolBar('Exit')
        # self.toolbar.addAction(exitAction)

        self.cWidget = RazorCentralWidget(self)

        self.setCentralWidget(self.cWidget)

        self.setGeometry(0, 900, 1920//3, 90)
        self.setWindowTitle(windowTitle)
        self.show()

    def frequentUpdate(self):
        self.redisplay()
        # self.updateStatusBarTimes()

    def redisplay(self):
        self.cWidget.redisplay()

    def updateStatusBarTimes(self):

        secondsSinceLastQuery = int(-self.cWidget.secondsSinceLastQuery())
        latestQueryTime = str(self.cWidget.latestQueryTime)[:-7]

        self.statusBar().showMessage(
            "last update was {} seconds ago at {}".format(
               secondsSinceLastQuery,
               latestQueryTime
            )
        )

def main():
    app = QtGui.QApplication(sys.argv)
    ex = RazorWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()