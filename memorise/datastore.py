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

from PyQt5 import QtSql
from PyQt5.QtCore import Qt, QIdentityProxyModel
import sys

dbschema = ["""
CREATE TABLE `memtableroot` (
        `Memory Set`    text NOT NULL,
        `Created`       INTEGER NOT NULL DEFAULT 0,
        `Archived`      TEXT,
        PRIMARY KEY(`Memory Set`)
)""","""
CREATE TABLE `tests` (
        `TestID`        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        `Memory Set`    TEXT NOT NULL,
        `TimeStamp`     INTEGER NOT NULL
)""","""
CREATE TABLE `answers` (
        `TestID`        INTEGER NOT NULL,
        `QuestionID`    INTEGER NOT NULL,
        `Column1`       TEXT NOT NULL,
        `Value1`        TEXT NOT NULL,
        `Column2`       TEXT NOT NULL,
        `UserAnswer`    TEXT NOT NULL,
        `CorrectAnswer` TEXT NOT NULL,
        PRIMARY KEY(`TestID`,`QuestionID`,`Column1`,`Value1`)
)""","""
CREATE VIEW `results` as
  SELECT t.`Memory Set`,a.TestID,a.Column1,a.Value1,a.Column2,a.UserAnswer,a.CorrectAnswer
  FROM answers AS a
  LEFT JOIN tests AS t ON a.TestID == t.TestID
"""
]

mainwindowquery = """
SELECT r.`Memory Set`,
(
  SELECT `TimeStamp`
  FROM
  (
    SELECT MAX(`TestID`),`TimeStamp`
        FROM `tests`
        WHERE `Memory Set` == r.`Memory Set`
  )
) AS `Last Used`,
(
  SELECT COUNT(`TestID`)
  FROM `tests`
  WHERE `tests`.`Memory Set` == r.`Memory Set`
) AS `Times Used`,
r.`Created`
FROM `memtableroot` AS r ORDER BY r.`Archived`
"""

class Datastore:
    def __init__(self, dbase='pymem.db'):
        self.dbase = dbase
        self.roottable = None

    def __enter__(self):
        self.db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(self.dbase)
        if not self.db.open():
            print("Error: Unable to open database.")
            sys.exit(1)
        query = QtSql.QSqlQuery(self.db)
        if not query.exec_("SELECT `Memory Set` FROM `memtableroot`"):
            print("Warning: Initilising database.")
            if any([not query.exec_(q) for q in dbschema]):
                print("Error: Unable to initilise database")
                sys.exit(1)
        return self

    def __exit__(self, type, value, tb):
        self.db.close()
        self.roottable = None

    def loadroottable(self):
        if not self.roottable:
            self.roottable = QtSql.QSqlQueryModel()
            self._reselectroottable()
        return self.roottable

    def _reselectroottable(self):
        self.roottable.setQuery(mainwindowquery)

    def loadtable(self, name, system=False):
        model = QtSql.QSqlTableModel(db = self.db)
        if system:
            model.setTable(name)
        else:
            model.setTable("_" + name)
        model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        if not model.select():
            print("Warning: Failed to select table {}".format(name))
            model.setHeaderData(0, Qt.Horizontal, "First")
            model.setHeaderData(1, Qt.Horizontal, "Second")
        return model

    def createtable(self, name, headings):
        query = QtSql.QSqlQuery(self.db)
        if query.prepare("INSERT INTO memtableroot (`Memory Set`, `Created`)"
                         " values (:name, DATETIME())"):
            query.bindValue(":name", name)
            if not query.exec_():
                print("Error: Failed to register table {}".format(name))
                return None
        else:
            print("Error: Failed to prepare query to"
                  " register table {}".format(name))
            return None
        self._reselectroottable()

        q = ("CREATE TABLE `_{}` ("
               "`{}` TEXT PRIMARY KEY NOT NULL"
               "".format(name, headings[0]))
        for hd in headings[1:]:
            q = q + ", `{}` TEXT".format(hd)
        q = q + ")"
        if not query.exec_(q):
            print("Error: Unable to create table {}".format(name))
            return None

        return self.loadtable(name)

    def droptable(self, name):
        query = QtSql.QSqlQuery(self.db)
        if query.prepare("DELETE FROM memtableroot "
                         "WHERE `Memory Set` == :name"):
            query.bindValue(":name", name)
            if not query.exec_():
                print("Error: Unable to unregister table {}".format(name))
                return None
        else:
            print("Error: Unable to prepare query to "
                  "unregister table {}".format(name))
            return None
        self._reselectroottable()

        query = QtSql.QSqlQuery(self.db)
        if not query.exec_("drop table `_{}`".format(name)):
            print("Error: Unable to drop table {}".format(name))
            return None

        return True

    def saveresults(self, name, results):
        query = QtSql.QSqlQuery(self.db)
        if query.prepare("INSERT INTO TESTS (`Memory Set`, `TimeStamp`) VALUES"
                         " (:name, DATETIME())"):
            query.bindValue(":name", name)
            if not query.exec_():
                print("Error: Failed to create test entry.")
                return False
            if not query.exec("SELECT MAX(TestId) FROM tests") or \
               not query.first():
                print("Error: Failed to get test entry.")
                return False
            testId = int(query.value(0))
            for i in range(0,len(results)):
                if query.prepare("INSERT INTO `answers` "
                                 "(`TestID`, `QuestionID`, `Column1`, `Value1`,"
                                 " `Column2`, `UserAnswer`, `CorrectAnswer`) "
                                 "VALUES (:id, :qid, :c1, :v1, :c2, :ua, :ca)"):
                    result = results[i]
                    query.bindValue(":id", testId)
                    query.bindValue(":qid", i)
                    query.bindValue(":c1", result[0])
                    query.bindValue(":v1", result[1])
                    query.bindValue(":c2", result[2])
                    query.bindValue(":ua", "\n".join(result[6]))
                    query.bindValue(":ca", "\n".join(result[5]))
                    if not query.exec_():
                        print("Error: Failed to create answer entry.")
                        return False
                else:
                    print("Error: Failed to prepare answer entry.")
                    return False
        else:
            print("Error: Failed to prepare test entry.")
            return False
        self._reselectroottable()
        return True
