# Copyright (C) 2019 Karim Kanso. All Rights Reserved.
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

from .ui.uiReviewDialog import Ui_ReviewDialog
from PyQt5.QtWidgets import QDialog, QHeaderView
from PyQt5.QtCore import QSortFilterProxyModel

class ReviewDialog(QDialog):
    def __init__(self, name, datastore):
        super().__init__()

        self.datastore = datastore

        self.ui = Ui_ReviewDialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Test Results Review: {}".format(name))

        self.ui.tests.header().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.ui.tests.setModel(self.datastore.loadreviewtests(name))
        self.ui.tests.selectionModel().selectionChanged.connect(self.select)
        self.ui.tests.hideColumn(0)

        self.ui.questions.header().setSectionResizeMode(
            QHeaderView.ResizeToContents)

    def select(self, selected, deslected):
        if len(selected.indexes()) > 0:
            row = selected.indexes()[0].row()
            testid = self.ui.tests.model().record(row).value("TestID")
            sortmodel = QSortFilterProxyModel()
            sortmodel.setSourceModel(self.datastore.loadreviewanswers(testid))
            self.ui.questions.setModel(sortmodel)
