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
from PyQt5.QtWidgets import QDialog, QHeaderView, QMenu
from PyQt5.QtCore import QSortFilterProxyModel
from functools import partial
from .questionReview import QuestionReviewDialog

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
        self.ui.questions.customContextMenuRequested.connect(self.popup)
        self.menudetails = QMenu()
        self.menudetails.addAction(self.ui.actionViewQuestionDetails)

    def select(self, selected, deslected):
        if len(selected.indexes()) > 0:
            row = selected.indexes()[0].row()
            testid = self.ui.tests.model().record(row).value("TestID")
            sortmodel = QSortFilterProxyModel()
            sortmodel.setSourceModel(self.datastore.loadreviewanswers(testid))
            self.ui.questions.setModel(sortmodel)
            self.ui.questions.hideColumn(0)

    def popup(self, pos):
        qi = self.ui.questions.indexAt(pos)
        if not self.ui.questions.model() or qi.row() < 0:
            return
        srcqi = self.ui.questions.model().mapToSource(qi)
        gpos = self.ui.questions.mapToGlobal(pos)
        self.ui.actionViewQuestionDetails.triggered.disconnect()
        self.ui.actionViewQuestionDetails.triggered.connect(
            partial(ReviewDialog.showquestion, self=self, qi=srcqi))
        if srcqi:
            self.menudetails.popup(gpos)

    def showquestion(self, qi):
        record = self.ui.questions.model().sourceModel().record(qi.row())
        review = QuestionReviewDialog(self.datastore.loadreviewanswersdetail(
            record.value("TestID"),
            record.value("QuestionID")))
        review.exec()
