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

from .ui.uiQuizDialog import Ui_QuizDialog
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from functools import partial
import random

class ChoiceModel(QStandardItemModel):
    def __init__(self, data):
        super().__init__(len(data),1)
        self.setHorizontalHeaderItem(0, QStandardItem("Choice"))
        for i in range(0,len(data)):
            item = QStandardItem(data[i])
            item.setCheckable(True)
            item.setCheckState(Qt.Unchecked)
            self.setItem(i, 0, item)

    def selectedItems(self):
        items = []
        for row in range(0, self.rowCount()):
            item = self.item(row)
            if item.checkState() == Qt.Checked:
                items.append(item.text())
        return items

class QuizDialog(QDialog):
    def __init__(self, name, tablemodel):
        super().__init__()

        self.ui = Ui_QuizDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Quiz: {}".format(name))

        self.ui.radioFreeText.toggled.connect(partial(self.showQuestion))
        self.ui.buttonNext.clicked.connect(self.endQuestion)

        self.questions = []
        self.question = None
        self.results = []

        self.buildQuiz(tablemodel)
        self.ui.progressBar.setMaximum(len(self.questions))
        self.showQuestion()

    def buildQuiz(self, model):
        data = lambda r, c: model.data(model.index(r, c))
        # iterate over columns
        r = model.record()
        quiz = {}
        values = {}
        for c1 in range(0, r.count()):
            c1name = r.fieldName(c1)
            for row in range(0, model.rowCount()):
                c1value = data(row, c1)
                if c1value != "":
                    if not values.get(c1name):
                        values[c1name] = []
                    if values[c1name].count(c1value) == 0:
                        values[c1name].append(c1value)
                    for c2 in range(0, r.count()):
                        if c2 != c1:
                            c2name = r.fieldName(c2)
                            c2value = data(row, c2)
                            if c2value != "":
                                if not quiz.get(c1name):
                                    quiz[c1name] = {}
                                if not quiz[c1name].get(c1value):
                                    quiz[c1name][c1value] = {}
                                if not quiz[c1name][c1value].get(c2name):
                                    quiz[c1name][c1value][c2name] = []
                                if quiz[c1name][c1value][c2name].count(c2value) == 0:
                                    quiz[c1name][c1value][c2name].append(c2value)

        self.questions = []
        for c1 in quiz.keys():
            for v1 in quiz[c1].keys():
                for c2 in quiz[c1][v1].keys():
                    self.questions.append((c1,v1,c2,quiz[c1][v1][c2],values[c2]))
        random.shuffle(self.questions)
        if len(self.questions) > 0:
            self.question = self.questions.pop()

    def showQuestion(self):
        if self.question:
            self.ui.progressBar.setValue(len(self.results))

            self.ui.labelHeading1.setText(self.question[0])
            self.ui.labelDataFrom1.setText(self.question[1])
            self.ui.labelHeading2.setText(self.question[2])

            self.ui.listAnswer.setModel(None)
            self.ui.textAnswer.clear()

            if self.ui.radioFreeText.isChecked():
                self.ui.listAnswer.setVisible(False)
                self.ui.textAnswer.setVisible(True)
            else:
                self.ui.listAnswer.setVisible(True)
                self.ui.textAnswer.setVisible(False)
                self.ui.listAnswer.setModel(ChoiceModel(self.question[4]))

    def endQuestion(self):
        if self.ui.radioFreeText.isChecked():
            answer = [ x.upper() for x in self.ui.textAnswer.toPlainText().split('\n') if x != '']
        else:
            answer = [ x.upper() for x in self.ui.listAnswer.model().selectedItems() ]
        answer.sort()
        correctanswers = [ x.upper() for x in self.question[3] ]
        correctanswers.sort()

        ok = True
        if len(answer) == len(correctanswers):
            for i in range(0,len(answer)):
                if answer[i] != correctanswers[i]:
                    ok = False
                    break
        else:
            ok = False

        msg = QMessageBox()
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setIcon(QMessageBox.Information)
        msg.setText("Well Done!")
        if not ok:
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Ignore)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("The correct answer is: \n{}".format("\n".join(self.question[3])))

        if msg.exec() == QMessageBox.Ignore:
            answer = correctanswers

        self.results.append(self.question + (correctanswers,answer,ok))

        if len(self.questions) > 0:
            self.question = self.questions.pop()
            self.showQuestion()
        else:
            msg = QMessageBox()
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setIcon(QMessageBox.Information)
            msg.setText("Test Finished")
            msg.exec()
            self.accept()
