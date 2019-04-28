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
from .edit import ErrorProxyModel
from PyQt5.QtWidgets import QDialog, QMenu
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPalette, QBrush
from PyQt5.QtCore import Qt
from functools import partial
import re

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

        ptablemodel = ErrorProxyModel()
        ptablemodel.setSourceModel(Headings())
        self.headings = ptablemodel
        self.ui.listHeadings.setModel(self.headings)

        self.ui.listHeadings.customContextMenuRequested.connect(self.popup)
        self.menuadd = QMenu()
        self.menuadd.addAction(self.ui.actionInsertColumnHeader)
        self.menuremove = QMenu()
        self.menuremove.addAction(self.ui.actionInsertColumnHeader)
        self.menuremove.addAction(self.ui.actionRemoveColumnHeader)

        self.ui.lineName.textChanged.connect(self.validatename)
        ptablemodel.dataChanged.connect(self.validatecell)
        ptablemodel.sourceModel().rowsInserted.connect(
            partial(AddDialog.validatecell,
                    self=self, tl=None, br=None, role=[]))
        ptablemodel.sourceModel().rowsRemoved.connect(
            partial(AddDialog.validatecell,
                    self=self, tl=None, br=None, role=[]))

        pal = QPalette()
        pal.setColor(QPalette.Mid, Qt.red)
        self.ui.lineName.setPalette(pal)
        self.ui.lineName.setAutoFillBackground(True)

        self._validateresult = { "name": False, "headings": True }
        self.validatename()

    def popup(self, pos):
        qi = self.ui.listHeadings.indexAt(pos)
        gpos = self.ui.listHeadings.viewport().mapToGlobal(pos)
        self.ui.actionInsertColumnHeader.triggered.disconnect()
        self.ui.actionInsertColumnHeader.triggered.connect(partial(AddDialog.insert, self=self, qi=qi))
        self.ui.actionRemoveColumnHeader.triggered.disconnect()
        self.ui.actionRemoveColumnHeader.triggered.connect(partial(AddDialog.remove, self=self, qi=qi))
        if qi.row() < 0:
            self.menuadd.popup(gpos)
        else:
            self.menuremove.popup(gpos)

    def insert(self, qi):
        row = qi.row()
        if row < 0:
            row = self.headings.rowCount()
        self.headings.sourceModel().insertRow(row,QStandardItem("NewItem"))

    def remove(self, qi):
        row = qi.row()
        if row < 0:
            return
        self.headings.sourceModel().removeRow(row)

    def validateresult(self, component, result):
        if self._validateresult.get(component) != None:
            self._validateresult[component] = result
        else:
            print("Ignoring validation result for component {}"
                  .format(component))

        for comp in self._validateresult:
            if not self._validateresult[comp]:
                self.ui.buttonBox.button(self.ui.buttonBox.Ok).setEnabled(False)
                return
        self.ui.buttonBox.button(self.ui.buttonBox.Ok).setEnabled(True)

    def validatename(self):
        def fail(msg, warning=False):
            print("Warning: Table Name Validation Fail: {}".format(msg))
            self.ui.lineName.setBackgroundRole(QPalette.Mid)
            self.validateresult("name", False)

        if self.tableName() == "":
            return fail("No table name")

        if self.tableName().startswith("_"):
            return fail("Tablename starts with underscore")

        # The table name needs to be constrained, otherwise QSqlTableModel
        # will fail to load the table.
        for c in self.tableName():
            if not c.isalnum() and not c in "_":
                return fail("Invalid char in table name")

        for tbl in self.existingtables:
            if tbl == self.tableName():
                return fail("Duplicate table name")

        if self.headings.rowCount() < 2:
            return fail("Not enough row headers")

        self.ui.lineName.setBackgroundRole(QPalette.NoRole)
        self.validateresult("name", True)

    def validatecell(self, tl = None, br = None, role = []):
        if (tl == None or tl.column() == 0) and role == []:
            ok = self.headings.rowCount() > 0
            seen = {}
            for row in range(0, self.headings.rowCount()):
                idx = self.headings.index(row, 0)
                val = self.headings.data(idx).strip()
                def fail(msg):
                    nonlocal ok
                    self.headings.setData(idx,
                                          QBrush(Qt.red),
                                          Qt.BackgroundRole)
                    ok = False
                    print("Warning: Column Validation Fail: {}".format(msg))

                if seen.get(val):
                    fail("Duplicate heading")
                    self.headings.setData(seen.get(val),
                                          QBrush(Qt.red),
                                          Qt.BackgroundRole)
                elif re.match(r"^[a-zA-Z0-9_\- ]+$", val):
                    self.headings.setData(idx, None, Qt.BackgroundRole)
                else:
                    fail("Invalid chars in heading")
                seen[val] = idx
            self.validateresult("headings", ok)

    def tableName(self):
        return self.ui.lineName.text().strip().replace(" ", "_")

    def columnHeadings(self):
        return [ self.headings.data(i).strip()
                 for r in range(0, self.headings.rowCount())
                 for i in [self.headings.index(r,0)] ]
