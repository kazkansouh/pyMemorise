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
from PyQt5.QtWidgets import QMainWindow, QDialog, QHeaderView
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QIdentityProxyModel
from PyQt5.QtGui import QBrush, QColor

name = "pyMemorise"

# number of test results to search for clean runs, used to colour
# items in main window.
window_size = 5

def interp(a = Qt.black, b = Qt.white, f = 0.5):
    return QColor(
        a.red() + int((b.red() - a.red()) * f),
        a.green() + int((b.green() - a.green()) * f),
        a.blue() + int((b.blue() - a.blue()) * f),
        a.alpha() + int((b.alpha() - a.alpha()) * f)
    )

class VisualPriorityProxyModel(QIdentityProxyModel):
    def __init__(self):
        super().__init__()

        first = QColor(255, 170, 170)
        last = QColor(170, 255, 170)

        self.colours = []
        for i in range(0,window_size + 1):
            self.colours.append(QBrush(interp(first, last, i/window_size)))

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.BackgroundRole:
            index.row()
            return self.colours[
                int(super().data(self.index(index.row(), 5), Qt.DisplayRole))]
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

        self.ui.buttonClose.clicked.connect(self.close)
        self.ui.buttonAdd.clicked.connect(self.add)
        self.ui.buttonRemove.clicked.connect(self.remove)
        self.ui.buttonEdit.clicked.connect(self.edit)
        self.ui.buttonStart.clicked.connect(self.start)
        self.ui.buttonReview.clicked.connect(self.review)

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

    def remove(self):
        for item in self.ui.table.selectionModel().selectedRows():
            self.datastore.droptable(self.ui.table.model().data(item))

    def edit(self):
        for item in self.ui.table.selectionModel().selectedRows():
            model = self.datastore.loadtable(self.ui.table.model().data(item))
            edit = EditDialog(model)
            edit.exec()

    def start(self):
        for item in self.ui.table.selectionModel().selectedRows():
            name = self.ui.table.model().data(item)
            model = self.datastore.loadtable(name, editable=False)
            quiz = QuizDialog(name, model)
            if quiz.exec() == QDialog.Accepted:
                self.datastore.saveresults(name, quiz.results)
            break

    def review(self):
        for item in self.ui.table.selectionModel().selectedRows():
            name = self.ui.table.model().data(item)
            review = ReviewDialog(name, self.datastore)
            review.exec()
            break

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        if event.key() == Qt.Key_Escape:
            self.close()
