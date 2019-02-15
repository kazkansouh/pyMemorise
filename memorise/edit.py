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

from .ui.uiEditDialog import Ui_EditDialog
from PyQt5.QtWidgets import QDialog, QMenu
from functools import partial

from PyQt5.QtCore import Qt, QIdentityProxyModel
from PyQt5.QtGui import QBrush
from PyQt5.QtSql import QSqlField

class ErrorProxyModel(QIdentityProxyModel):
    def __init__(self):
        super().__init__()

        self.mapping = []

    def setData(self, index, value, role=Qt.EditRole):
        if index.column() == 0 and role == Qt.BackgroundRole:
            self.mapping[index.row()] = value
            self.dataChanged.emit(index, index, [Qt.BackgroundRole])
            return True
        return super().setData(index, value, role)

    def data(self, index, role=Qt.DisplayRole):
        if index.column() == 0 and role == Qt.BackgroundRole:
            return self.mapping[index.row()]
        return super().data(index, role)

    def rowInsert(self, p, first, last):
        for k in range(first, last+1):
            self.mapping.insert(first, None)

    def rowRemove(self, p, first, last):
        for k in range(first, last+1):
            self.mapping = self.mapping[:first] + self.mapping[last + 1:]

    def setSourceModel(self,model):
        model.rowsAboutToBeInserted.connect(self.rowInsert)
        model.rowsAboutToBeRemoved.connect(self.rowRemove)
        self.mapping = [None for x in range(0, model.rowCount())]
        return super().setSourceModel(model)

class EditDialog(QDialog):
    def __init__(self, tablemodel):
        super().__init__()

        self.ui = Ui_EditDialog()
        self.ui.setupUi(self)

        ptablemodel = ErrorProxyModel()
        ptablemodel.setSourceModel(tablemodel)
        self.ui.table.setModel(ptablemodel)

        self.ui.table.customContextMenuRequested.connect(self.popup)
        self.menuadd = QMenu()
        self.menuadd.addAction(self.ui.actionAddRow)
        self.menuremove = QMenu()
        self.menuremove.addAction(self.ui.actionAddRow)
        self.menuremove.addAction(self.ui.actionRemoveRow)
        self.ui.buttonBox.accepted.connect(self.accepted)

        ptablemodel.dataChanged.connect(self.validatecell)

    def popup(self, pos):
        qi = self.ui.table.indexAt(pos)
        gpos = self.ui.table.viewport().mapToGlobal(pos)
        self.ui.actionAddRow.triggered.disconnect()
        self.ui.actionAddRow.triggered.connect(partial(EditDialog.add, self=self, qi=qi))
        self.ui.actionRemoveRow.triggered.disconnect()
        self.ui.actionRemoveRow.triggered.connect(partial(EditDialog.remove, self=self, qi=qi))
        if qi.row() < 0:
            self.menuadd.popup(gpos)
        else:
            self.menuremove.popup(gpos)

    def validatecell(self, tl, br, role):
        if tl.column() == 0 and role == []:
            seen = {}
            self.ui.buttonBox.button(self.ui.buttonBox.Ok).setEnabled(self.ui.table.model().rowCount() > 0)
            for row in range(0, self.ui.table.model().rowCount()):
                idx = self.ui.table.model().index(row, 0)
                val = self.ui.table.model().data(idx)
                if val == "":
                    self.ui.table.model().setData(idx, QBrush(Qt.red), Qt.BackgroundRole)
                    self.ui.buttonBox.button(self.ui.buttonBox.Ok).setEnabled(False)
                elif seen.get(val):
                    self.ui.buttonBox.button(self.ui.buttonBox.Ok).setEnabled(False)
                    self.ui.table.model().setData(idx, QBrush(Qt.red), Qt.BackgroundRole)
                    self.ui.table.model().setData(seen.get(val), QBrush(Qt.red), Qt.BackgroundRole)
                else:
                    self.ui.table.model().setData(idx, None, Qt.BackgroundRole)
                seen[val] = idx

    def add(self, qi):
        self.ui.table.model().sourceModel().insertRecord(qi.row(),self.ui.table.model().sourceModel().record())

    def remove(self, qi):
        self.ui.table.model().sourceModel().removeRow(qi.row())

    def accepted(self):
        self.ui.table.model().sourceModel().submitAll()
