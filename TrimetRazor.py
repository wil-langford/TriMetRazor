#!/usr/bin/env python

import sys
from PyQt4 import QtGui, QtCore
import Razors


class RazorListModel(QtCore.QAbstractListModel):
    def __init__(self, stopID, parent=None):
        super(RazorListModel, self).__init__()
        self.stopID = stopID
        self.tmr = Razors.StreetcarRazor(stopID)
        self.updateTimes()

        self.maxSeconds = 60
        self.fullBarWidth = 500
        self.rowHeight = 6

    def secondsToPixels(self, s):
        m = max(self._times)
        if self.maxSeconds < m:
            self.maxSeconds = m
        return int((self.fullBarWidth-30)*s/self.maxSeconds)

    def _refresh_times_from_razor(self):
        self._times = [int(x[0]) for x in self.tmr.next_up() if 'NS' in x[1]]

    def updateTimes(self):
        self.beginResetModel()
        self.tmr.query_arrivals()
        self._refresh_times_from_razor()
        print self._times
        self.endResetModel()

    def emitAllDataChanged(self):
        if self._times is not None and min(self._times)<=0:
            self.updateTimes()
        else:
            self.dataChanged.emit(self.first(), self.last())

    def first(self):
        return self.createIndex(0,0)

    def last(self):
        return self.createIndex(self.rowCount()-1,0)

    def rowCount(self, QModelIndex_parent=None, *args, **kwargs):
        if self._times is None:
            return 2
        else:
            return len(self._times) + 1

    def data(self, QModelIndex, int_role=None):
        self._refresh_times_from_razor()
        row = QModelIndex.row()

        if int_role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(500,self.rowHeight+2)

        if row < self.rowCount()-1:
            if int_role == QtCore.Qt.DisplayRole:
                if self._times is None:
                    return "No estimated arrivals."
                min, sec = divmod(int(self._times[row]), 60)
                return "{}:{:02d}".format(min,sec)

            if int_role == QtCore.Qt.DecorationRole:
                if self._times is None:
                    pixmap = QtGui.QPixmap(self.rowHeight,self.rowHeight)
                    pixmap.fill(QtGui.QColor(200,200,200))
                    return pixmap
                timeleft = self._times[row]

                if timeleft > 10*60:
                    color = QtGui.QColor(0,150,0)
                elif timeleft < 6*60:
                    color = QtGui.QColor(150,0,0)
                else:
                    color = QtGui.QColor(220,220,0)

                pixmap = QtGui.QPixmap(
                    self.secondsToPixels(self._times[row]),
                    self.rowHeight)
                pixmap.fill(color)
                return pixmap
        else:
            sec = -int(self.tmr.time_since_last_query())

            if int_role == QtCore.Qt.DisplayRole:
                return "seconds since last query: {}".format(sec)

            if int_role == QtCore.Qt.DecorationRole:
                if sec < 60:
                    color = QtGui.QColor(0,150,0)
                elif sec > 70:
                    color = QtGui.QColor(150,0,0)
                else:
                    color = QtGui.QColor(220,220,0)

                pixmap = QtGui.QPixmap(self.rowHeight,
                                       self.rowHeight)
                pixmap.fill(color)
                return pixmap


class RazorListView(QtGui.QListView):
    def __init__(self, parent=None):
        super(RazorListView, self).__init__(parent=parent)
        self.parent=parent

    def mousePressEvent(self, QMouseEvent):
        self.offset = QMouseEvent.pos()

    def mouseMoveEvent(self, QMouseEvent):
        x, y=QMouseEvent.globalX(), QMouseEvent.globalY()
        x_w, y_w = self.offset.x(), self.offset.y()
        self.parent.move(x-x_w, y-y_w)

    def mouseDoubleClickEvent(self, QMouseEvent):
        self.model().updateTimes()


class RazorThinWidget(QtGui.QWidget):
    def __init__(self, parent=None, stopID=10760):
        super(RazorThinWidget, self).__init__()

        self.cTimer = QtCore.QTimer()
        self.uiTimer = QtCore.QTimer()
        self.qTimer = QtCore.QTimer()

        # self.timesModel=RazorListModel(stopID=10751, parent=self)
        self.timesModel=RazorListModel(stopID=stopID, parent=self)

        self.secondsSinceLastQuery = self.timesModel.tmr.time_since_last_query
        self.latestQueryTime = self.timesModel.tmr.time_since_last_query()

        self.updateFrequency = 60
        self.redisplayFrequency = 1
        self.quitAfterSeconds = 120*60 # two hours

        self.showFrame = False

        self.initUI()

    def initUI(self):

        vBox = QtGui.QVBoxLayout()

        self.listView = RazorListView(self)
        self.listView.setModel(self.timesModel)
        self.listView.setContentsMargins(0,0,0,0)
        self.listView.setMinimumSize(QtCore.QSize(200,10))
        self.listView.setStyleSheet('''
                QWidget {
                   background-color: black;
                   color: white;
                   font-size: 6pt;
                }
                ''')

        vBox.addWidget(self.listView, 1)
        vBox.setContentsMargins(0,0,0,0)

        self.cTimer.start(self.updateFrequency*1000)
        self.cTimer.timeout.connect(self.updateTimes)

        self.uiTimer.start(self.redisplayFrequency*1000)
        self.uiTimer.timeout.connect(self.redisplay)

        self.qTimer.start(self.quitAfterSeconds*1000)
        self.qTimer.timeout.connect(QtGui.qApp.quit)

        self.setLayout(vBox)

        self.setGeometry(0, 530, 530, 26)
        self.setWindowFlags(self.windowFlags()
                            | QtCore.Qt.WindowStaysOnTopHint
                            | QtCore.Qt.FramelessWindowHint
        )
        self.setWindowTitle('TriMet Razor')

        quitShortcut = QtGui.QShortcut(self)
        quitShortcut.setKey("Ctrl+Q")
        quitShortcut.setContext(QtCore.Qt.ApplicationShortcut)
        quitShortcut.activated.connect(QtGui.qApp.quit)

        requeryShortcut = QtGui.QShortcut(self)
        requeryShortcut.setKey("Ctrl+R")
        requeryShortcut.setContext(QtCore.Qt.ApplicationShortcut)
        requeryShortcut.activated.connect(self.updateTimes)

        self.show()

    def updateTimes(self):
        self.timesModel.updateTimes()

    def redisplay(self):
        self.timesModel.emitAllDataChanged()
        self.resize(530,self.timesModel.rowCount()*(self.timesModel.rowHeight+2)+4)

    def toggleFrame(self):
        if self.showFrame:
            self.setWindowFlags(
                self.windowFlags()
                & ~QtCore.Qt.FramelessWindowHint)
            self.showFrame=False
        else:
            self.setWindowFlags(
                self.windowFlags()
                | QtCore.Qt.FramelessWindowHint)
            self.showFrame=True


def main():
    app = QtGui.QApplication(sys.argv)
    app.setStyle("cleanlooks")
    ex = RazorThinWidget(stopID=10760)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()