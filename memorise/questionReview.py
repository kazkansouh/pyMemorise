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

from .ui.uiQuestionReviewDialog import Ui_QuestionReviewDialog
from PyQt5.QtWidgets import QDialog, QHeaderView
from PyQt5.QtCore import QSortFilterProxyModel

class QuestionReviewDialog(QDialog):
    def __init__(self, model):
        super().__init__()

        self.ui = Ui_QuestionReviewDialog()
        self.ui.setupUi(self)

        self.ui.questions.header().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.ui.questions.setModel(model)
        self.ui.questions.selectionModel().selectionChanged.connect(self.select)
        self.ui.questions.hideColumn(0)
        self.ui.questions.hideColumn(1)
        self.ui.questions.hideColumn(2)
        self.ui.questions.hideColumn(3)
        self.ui.questions.hideColumn(4)

        self.ui.questions.header().setSectionResizeMode(
            QHeaderView.ResizeToContents)

    def select(self, selected, deslected):
        if len(selected.indexes()) > 0:
            row = selected.indexes()[0].row()
            model = self.ui.questions.model()
            testid = model.record(row).value("TestID")
            questionid = model.record(row).value("QuestionID")
            column1 = model.record(row).value("Column1")
            value1 = model.record(row).value("Value1")
            column2 = model.record(row).value("Column2")
            correctanswer = model.record(row).value("CorrectAnswer")
            useranswer = model.record(row).value("UserAnswer")

            self.ui.labelQuestion.setText(
                "Values from column {} that have the value {} in column {}:"
                "".format(column2, value1, column1))
            self.ui.correctAnswer.setPlainText(correctanswer)
            self.ui.userAnswer.setPlainText(useranswer)
