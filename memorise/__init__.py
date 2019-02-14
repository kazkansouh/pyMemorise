# Copyright (C) 2018 Karim Kanso. All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .ui.uiMainWindow import Ui_MainWindow
from .add import AddDialog
from .edit import EditDialog
from .quiz import QuizDialog
from .review import ReviewDialog
from PyQt5.QtWidgets import QMainWindow, QDialog, QHeaderView, QMenu
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QIdentityProxyModel
from PyQt5.QtGui import QBrush, QColor
import math
from functools import partial

name = "pyMemorise"

# number of test results to search for clean runs, used to colour
# items in main window.
window_size = 5

def weight(f):
    "Weighted map [0,1] |-> [0,1] used for selecting colour"
    return math.pow(f,20)

def interp(a = Qt.black, b = Qt.white, f = 0.5):
    "Interpolate colour"
    return QColor(
        a.red() + int((b.red() - a.red()) * f),
        a.green() + int((b.green() - a.green()) * f),
        a.blue() + int((b.blue() - a.blue()) * f),
        a.alpha() + int((b.alpha() - a.alpha()) * f)
    )

class VisualPriorityProxyModel(QIdentityProxyModel):
    def __init__(self):
        super().__init__()

        self.first = QColor(255, 170, 170)
        self.last = QColor(170, 255, 170)
        self.colours = {}

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.BackgroundRole:
            correct = super().data(self.index(index.row(), 6), Qt.DisplayRole)
            incorrect = super().data(self.index(index.row(), 7), Qt.DisplayRole)
            if correct == 0:
                return self.first
            w = weight(correct/(correct+incorrect))
            colour = self.colours.get(w)
            if colour != None:
                return colour
            colour = QBrush(interp(self.first, self.last, w))
            self.colours[w] = colour
            return colour
        return super().data(index, role)


class Memorise(QMainWindow):
    def __init__(self, datastore):
        super().__init__()

        self.datastore = datastore

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.table.header().setSectionResizeMode(QHeaderView.ResizeToContents)

        sortmodel = QSortFilterProxyModel()
        sortmodel.setSourceModel(self.datastore.loadroottable(window_size))
        prioritymodel = VisualPriorityProxyModel()
        prioritymodel.setSourceModel(sortmodel)
        self.ui.table.setModel(prioritymodel)
        self.ui.table.sortByColumn(1, Qt.AscendingOrder)

        self.ui.table.customContextMenuRequested.connect(self.popup)
        self.menuexisting = QMenu()
        self.menuexisting.addAction(self.ui.actionBeginTest)
        self.menuexisting.addAction(self.ui.actionReviewPreviousAnswers)
        self.menuexisting.addSeparator()
        self.menuexisting.addAction(self.ui.actionEditMemorySet)
        self.menuexisting.addAction(self.ui.actionRemoveMemorySet)
        self.menuexisting.addSeparator()
        self.menuexisting.addAction(self.ui.actionAddNewMemorySet)
        self.menunew = QMenu()
        self.menunew.addAction(self.ui.actionAddNewMemorySet)
        self.ui.actionAddNewMemorySet.triggered.connect(self.add)

        self.ui.buttonClose.clicked.connect(self.close)
        self.ui.buttonAdd.clicked.connect(self.add)

    def popup(self, pos):
        qi = self.ui.table.model().index(self.ui.table.indexAt(pos).row(), 0)
        gpos = self.ui.table.viewport().mapToGlobal(pos)
        self.ui.actionBeginTest.triggered.disconnect()
        self.ui.actionEditMemorySet.triggered.disconnect()
        self.ui.actionReviewPreviousAnswers.triggered.disconnect()
        self.ui.actionRemoveMemorySet.triggered.disconnect()

        self.ui.actionBeginTest.triggered.connect(
            partial(Memorise.start, self=self, qi=qi))
        self.ui.actionEditMemorySet.triggered.connect(
            partial(Memorise.edit, self=self, qi=qi))
        self.ui.actionReviewPreviousAnswers.triggered.connect(
            partial(Memorise.review, self=self, qi=qi))
        self.ui.actionRemoveMemorySet.triggered.connect(
            partial(Memorise.remove, self=self, qi=qi))

        if qi.row() < 0:
            self.menunew.popup(gpos)
        else:
            self.menuexisting.popup(gpos)

    def add(self):
        add = AddDialog([ self.ui.table.model().data(i)
                          for r in range(0, self.ui.table.model().rowCount())
                          for i in [self.ui.table.model().index(r,0)] ])

        result = add.exec()
        if result == QDialog.Accepted:
            model = self.datastore.createtable(add.tableName(),
                                               add.columnHeadings())
            edit = EditDialog(model)
            result = edit.exec()
            if result == QDialog.Accepted:
                pass

    def remove(self, qi):
        name = self.ui.table.model().data(qi)
        msg = QMessageBox()
        msg.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Delete Memory Set")
        msg.setText("Are you sure you want to delete {}?".format(name))
        if msg.exec() == QMessageBox.Yes:
            self.datastore.droptable(name)

    def edit(self, qi):
        model = self.datastore.loadtable(self.ui.table.model().data(qi))
        edit = EditDialog(model)
        edit.exec()

    def start(self, qi):
        name = self.ui.table.model().data(qi)
        model = self.datastore.loadtable(name, editable=False)
        quiz = QuizDialog(name, model)
        if quiz.exec() == QDialog.Accepted:
            self.datastore.saveresults(name, quiz.results)

    def review(self, qi):
        name = self.ui.table.model().data(qi)
        review = ReviewDialog(name, self.datastore)
        review.exec()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        if event.key() == Qt.Key_Escape:
            self.close()
