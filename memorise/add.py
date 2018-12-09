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

from .ui.uiAddDialog import Ui_AddDialog
from PyQt5.QtWidgets import QDialog, QMenu
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from functools import partial

class Headings(QStandardItemModel):
    def __init__(self):
        super().__init__(2,1)
        self.setHorizontalHeaderItem(0, QStandardItem("Heading"))
        self.setItem(0, 0, QStandardItem("Heading1"))
        self.setItem(1, 0, QStandardItem("Heading2"))

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled

class AddDialog(QDialog):
    def __init__(self, existingtables):
        super().__init__()

        self.existingtables = existingtables

        self.ui = Ui_AddDialog()
        self.ui.setupUi(self)

        self.headings = Headings()
        self.ui.listHeadings.setModel(self.headings)

        self.ui.listHeadings.customContextMenuRequested.connect(self.popup)
        self.menuadd = QMenu()
        self.menuadd.addAction(self.ui.actionInsertColumnHeader)
        self.menuremove = QMenu()
        self.menuremove.addAction(self.ui.actionInsertColumnHeader)
        self.menuremove.addAction(self.ui.actionRemoveColumnHeader)

        self.ui.lineName.textChanged.connect(partial(AddDialog.validate, self=self))
        self.headings.itemChanged.connect(partial(AddDialog.validate, self=self))
        self.headings.rowsInserted.connect(partial(AddDialog.validate, self=self))
        self.headings.rowsRemoved.connect(partial(AddDialog.validate, self=self))

        self.validate()

    def popup(self, pos):
        qi = self.ui.listHeadings.indexAt(pos)
        i = self.headings.itemFromIndex(qi)
        gpos = self.ui.listHeadings.mapToGlobal(pos)
        self.ui.actionInsertColumnHeader.triggered.disconnect()
        self.ui.actionInsertColumnHeader.triggered.connect(partial(AddDialog.insert, self=self, qi=qi))
        self.ui.actionRemoveColumnHeader.triggered.disconnect()
        self.ui.actionRemoveColumnHeader.triggered.connect(partial(AddDialog.remove, self=self, qi=qi))
        if not i:
            self.menuadd.popup(gpos)
        else:
            self.menuremove.popup(gpos)

    def insert(self, qi):
        row = qi.row()
        if row < 0:
            row = self.headings.rowCount()
        self.headings.insertRow(row,QStandardItem("NewItem"))

    def remove(self, qi):
        row = qi.row()
        if row < 0:
            return
        self.headings.removeRow(row)

    def validate(self):
        def fail(msg):
            print(msg)
            self.ui.buttonBox.button(self.ui.buttonBox.Ok).setEnabled(False)
            return False

        if self.tableName() == "":
            return fail("No table name")

        for c in self.tableName():
            if not c == "_" and not c.isalnum():
                return fail("Invalid char in table name")

        for tbl in self.existingtables:
            if tbl == self.tableName():
                return fail("Duplicate table name")

        if self.headings.rowCount() < 2:
            return fail("Not enough row headers")

        for row in range(0,self.headings.rowCount()):
            item = self.headings.item(row).text().strip()
            if item == "":
                return fail("Empty heading")

            for c in item:
                if not c in "_ " and \
                   not c.isalnum():
                    return fail("Invalid char in heading")

            for prevrow in range(0,row):
                previtem = self.headings.item(prevrow)
                if item.upper() == previtem.text().strip().upper():
                    return fail("Duplicate heading")

        self.ui.buttonBox.button(self.ui.buttonBox.Ok).setEnabled(True)
        return True


    def tableName(self):
        return self.ui.lineName.text()

    def columnHeadings(self):
        return [ self.headings.data(i).strip()
                 for r in range(0, self.headings.rowCount())
                 for i in [self.headings.index(r,0)] ]
