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
import os
import ctypes

dbschema = ["""
CREATE TABLE `memtableroot` (
        `Memory Set`    text NOT NULL,
        `Created`       INTEGER NOT NULL DEFAULT 0,
        `Archived`      TEXT,
        `Revision`      INTEGER NOT NULL,
        PRIMARY KEY(`Memory Set`)
)""","""
CREATE TABLE `tests` (
        `TestID`        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        `Memory Set`    TEXT NOT NULL,
        `Revision`      INTEGER NOT NULL,
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
  SELECT t.`Memory Set`,
         a.TestID,
         a.Column1,
         a.Value1,
         a.Column2,
         a.UserAnswer,
         a.CorrectAnswer
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
r.`Created`,
r.`Revision`,
(
  /* Need to place SUM outside below SELECT as it ignores the LIMIT clause */
  SELECT COALESCE(SUM(`X`.`x`), 0) FROM
  (
    SELECT (
      SELECT CASE WHEN COUNT(`A`.`TestID`) == 0 THEN 1 ELSE 0 END
      FROM `answers` as `A`
      WHERE `A`.`TestID` == `T`.`TestID` AND
            `A`.`UserAnswer` != `A`.`CorrectAnswer`
    ) as `x`
    FROM `tests` AS `T`
    WHERE `T`.`Memory Set` == `r`.`Memory Set`
    ORDER BY `T`.`TimeStamp`
    DESC LIMIT :limit
  ) AS `X`
) AS `Perfect Runs in Window`,
(
  SELECT COALESCE(COUNT(`A`.`TestID`), 0)
  FROM
  (
    SELECT `T1`.`TestID`
    FROM `tests` as `T1`
    WHERE `T1`.`Memory Set` == `r`.`Memory Set`
    ORDER BY `T1`.`TimeStamp`
    DESC LIMIT :limit
  ) AS `T2`
  LEFT JOIN `answers` AS `A` ON `A`.`TestID` == `T2`.`TestID`
  WHERE `A`.`UserAnswer` == `A`.`CorrectAnswer`
) AS `Correct Answers in Window`,
(
  SELECT COALESCE(COUNT(`A`.`TestID`), 0)
  FROM
  (
    SELECT `T1`.`TestID`
    FROM `tests` as `T1`
    WHERE `T1`.`Memory Set` == `r`.`Memory Set`
    ORDER BY `T1`.`TimeStamp`
    DESC LIMIT :limit
  ) AS `T2`
  LEFT JOIN `answers` AS `A` ON `A`.`TestID` == `T2`.`TestID`
  WHERE `A`.`UserAnswer` != `A`.`CorrectAnswer`
) AS `Incorrect Answers in Window`
FROM `memtableroot` AS r ORDER BY r.`Archived`
"""

reviewdialogquery_tests = """
SELECT T.TestID, T.Revision, T.TimeStamp as `Time`,
(
  SELECT COUNT(TestID)
  FROM answers as A
  WHERE A.TestID == T.TestID AND A.UserAnswer == A.CorrectAnswer
) AS `Correct`,
(
  SELECT COUNT(TestID)
  FROM answers as A
  WHERE A.TestID == T.TestID AND A.UserAnswer != A.CorrectAnswer
) AS `Wrong`
FROM tests as T
WHERE T.`Memory Set` == :name
ORDER BY T.TimeStamp DESC
"""

reviewdialogquery_answers = """
SELECT
A.TestID,
A.QuestionID,
A.Column1 AS `Question Column`,
A.Value1 AS `Question Value`,
A.Column2 AS `Answer Column`,
(
  CASE WHEN A.CorrectAnswer == A.UserAnswer
  THEN "PASS"
  ELSE "FAIL" END
) AS Result,
(
  SELECT COUNT(*)
  FROM answers AS B
  WHERE B.Column1 == A.Column1 AND
        B.Value1 == A.Value1 AND
        B.Column2 == A.Column2 AND
        B.CorrectAnswer == A.CorrectAnswer
) AS `Times Asked`,
(
  SELECT COUNT(*)
  FROM answers AS B
  WHERE B.Column1 == A.Column1 AND
        B.Value1 == A.Value1 AND
        B.Column2 == A.Column2 AND
        B.CorrectAnswer == A.CorrectAnswer AND
        B.CorrectAnswer != B.UserAnswer
) AS `Times Failed`
FROM `answers` as A WHERE TestID == :testid
"""

reviewquestiondialogquery = """
SELECT
A.Column1,
A.Value1,
A.Column2,
A.CorrectAnswer,
A.UserAnswer,
A.TestID,
A.QuestionID,
T.TimeStamp AS Time,
(
  CASE WHEN A.CorrectAnswer == A.UserAnswer
  THEN "PASS"
  ELSE "FAIL" END
) AS Result
FROM answers AS A INNER JOIN tests AS T ON A.TestID == T.TestID
WHERE (A.Column1, A.Value1, A.Column2, A.CorrectAnswer) IN
(
  SELECT B.Column1, B.Value1, B.Column2, B.CorrectAnswer
  FROM answers AS B
  WHERE B.TestID == :testid AND B.QuestionID == :questionid
)
ORDER BY T.TimeStamp DESC
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
            if os.name == 'nt':
                ret = ctypes.windll.kernel32.SetFileAttributesW(self.dbase, 0x02)
                if not ret: # There was an error.
                    raise ctypes.WinError()
        return self

    def __exit__(self, type, value, tb):
        self.db.close()
        self.roottable = None

    def loadroottable(self, window_size = 5):
        if not self.roottable:
            self.roottable = QtSql.QSqlQueryModel()

        if not hasattr(self, 'window_size') or self.window_size != window_size:
            self.window_size = window_size
            return self._reselectroottable()

        return self.roottable

    def _reselectroottable(self):
        query = QtSql.QSqlQuery(self.db)
        if query.prepare(mainwindowquery):
            query.bindValue(":limit", self.window_size)
            if not query.exec_():
                print("Error: could not load main table query")
                return None
            self.roottable.setQuery(query)
            return self.roottable
        else:
            print("Error: could not prepare query to load "
                  "test data for {}".format(name))
            return None

    def loadreviewtests(self, name):
        query = QtSql.QSqlQuery(self.db)
        if query.prepare(reviewdialogquery_tests):
            query.bindValue(":name", name)
            if not query.exec_():
                print("Error: could not load test data for {}".format(name))
                return None
            table = QtSql.QSqlQueryModel()
            table.setQuery(query)
            return table
        else:
            print("Error: could not prepare query to load "
                  "test data for {}".format(name))
            return None

    def loadreviewanswers(self, testid):
        query = QtSql.QSqlQuery(self.db)
        if query.prepare(reviewdialogquery_answers):
            query.bindValue(":testid", testid)
            if not query.exec_():
                print("Error: could not load answers for "
                      "testid {}".format(testid))
                return None
            table = QtSql.QSqlQueryModel()
            table.setQuery(query)
            return table
        else:
            print("Error: could not prepare query to load "
                  "answers for testid {}".format(testid))
            return None

    def loadreviewanswersdetail(self, testid, questionid):
        query = QtSql.QSqlQuery(self.db)
        if query.prepare(reviewquestiondialogquery):
            query.bindValue(":testid", testid)
            query.bindValue(":questionid", questionid)
            if not query.exec_():
                print("Error: could not load answers for "
                      "testid {}, questionid {}".format(testid, questionid))
                return None
            table = QtSql.QSqlQueryModel()
            table.setQuery(query)
            return table
        else:
            print("Error: could not prepare query to load "
                  "answers for testid {}, questionid {}"
                  "".format(testid, questionid))
            return None

    def loadtable(self, name, editable=True):
        """Load a datatable from the database into an item model. If editable,
is selected and a test has already been run against the revision a
copy of the table is taken and revision incremented.

In the background, either QSqlQueryModel or QSqlTabelModel is used.

        """
        query = QtSql.QSqlQuery(self.db)
        ## First: Identify whether revision is used
        if query.prepare(
                "SELECT COUNT(t.`Revision`) > 0 AS Used,r.`Revision` "
                "FROM memtableroot AS r "
                "  LEFT JOIN tests AS t ON "
                "    r.`Memory Set` == t.`Memory Set` AND "
                "    r.`Revision` == t.`Revision` "
                "WHERE r.`Memory Set` == :name"):
            query.bindValue(":name", name)
            if not query.exec_():
                print("Error: Failed to check if table {} "
                      "is registered".format(name))
                return None
            if query.first():
                used = int(query.value(0)) > 0
                if query.value(1) == None:
                    print("Error: Table {} does not exist".format(name))
                    return None
                revision = int(query.value(1))
            else:
                # Should not occour due to use of COUNT
                print("Error: Failed to retreive result.")
                return None
        else:
            print("Error: Failed to prepare statment to check if "
                  "table {} is registerd.".format(name))
            return None

        ## Second: If revision used and edit is requested, create new
        ## table.
        if used and editable:
            return self.createtable(name)

        ## Third: Load the data
        if editable:
            model = QtSql.QSqlTableModel(db = self.db)
            model.setTable("_{}_{}".format(name, str(revision)))
            model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
            if not model.select():
                print("Warning: Failed to select table {}".format(name))
                model.setHeaderData(0, Qt.Horizontal, "First")
                model.setHeaderData(1, Qt.Horizontal, "Second")
            return model
        else:
            model = QtSql.QSqlQueryModel()
            model.setQuery("SELECT * FROM _{}_{}".format(name, revision))
            return model

    def createtable(self, name, headings=None):
        """Creates a database table and returns it loaded into a
QSqlTableModel.

If the table already exits, a new table is created with an incremented
revision.

If table does not exist, table is created from the headings specified
in headings.

        """
        query = QtSql.QSqlQuery(self.db)

        ## First: Check if table is already registerd and determine
        ## revision of table.
        if query.prepare("SELECT Revision "
                         "FROM memtableroot "
                         "WHERE `Memory Set` == :name"):
            query.bindValue(":name", name)
            if not query.exec_():
                print("Error: Failed to check if table {} "
                      "is registered".format(name))
                return None
            revision = 1
            if query.first():
                revision = int(query.value(0)) + 1
            if revision == 1 and headings == None:
                print("Error: Table and headings are undefined")
                return None
        else:
            print("Error: Failed to prepare statment to check if "
                  "table {} is registerd.".format(name))
            return None

        ## Second: Register table revision
        registersql = """
            INSERT INTO memtableroot (`Memory Set`, `Created`, `Revision`)
            VALUES (:name, DATETIME(), :rev)
        """
        if revision != 1:
            registersql = """
                UPDATE memtableroot SET `Revision` = :rev
                WHERE `Memory Set` == :name
            """

        if query.prepare(registersql):
            query.bindValue(":name", name)
            query.bindValue(":rev", revision)

            if not query.exec_():
                print("Error: Failed to register table {}".format(name))
                return None
        else:
            print("Error: Failed to prepare query to"
                  " register table {}".format(name))
            return None
        self._reselectroottable()

        ## Third: Create table
        if revision != 1:
            if not query.exec_("PRAGMA table_info(_{}_1)".format(name)):
                print("Error: Unable to read table info for _{}_1"
                      "".format(name))
                return None
            headings = []
            while query.next():
                headings.append(query.value("name"))

        q = ("CREATE TABLE `_{}_{}` ("
             "  `{}` TEXT PRIMARY KEY NOT NULL"
             "".format(name, revision, headings[0]))
        for hd in headings[1:]:
            q = q + ", `{}` TEXT".format(hd)
        q = q + ")"
        if not query.exec_(q):
            print("Error: Unable to create table {}".format(name))
            return None

        ## Forth: Copy values into new table
        if revision > 1:
            if not query.exec_(
                    "INSERT INTO _{name}_{r2} "
                    "SELECT * FROM _{name}_{r1}"
                    "".format(name=name, r1=revision-1, r2=revision)):
                print("Error: Unable to copy values into table")
                return None
        return self.loadtable(name)

    def droptable(self, name):
        "Drops and unregisters a table and all its revisions."
        query = QtSql.QSqlQuery(self.db)

        ## First: Check if table is registerd and determine revision
        ## of table.
        if query.prepare("SELECT Revision "
                         "FROM memtableroot "
                         "WHERE `Memory Set` == :name"):
            query.bindValue(":name", name)
            if not query.exec_():
                print("Error: Failed to check if table {} "
                      "is registered".format(name))
                return None
            if not query.first():
                print("Error: Can not drop unregistered table {}".format(name))
                return None
            revision = int(query.value(0))
        else:
            print("Error: Failed to prepare statment to check if "
                  "table {} is registerd.".format(name))
            return None

        ## Second: Unregister table
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

        ## Third: Drop all revisions
        for rev in range(1,revision+1):
            if not query.exec_("DROP TABLE `_{}_{}`".format(name, rev)):
                print("Warning: Unable to drop table _{}_{}".format(name, rev))

        ## Forth: Clear tests
        if query.prepare(
                "DELETE FROM answers "
                "WHERE answers.TestID IN ( "
                "    SELECT TestID "
                "    FROM tests "
                "    WHERE tests.`Memory Set` == :name "
                ")"):
            query.bindValue(":name", name)
            if not query.exec_():
                print("Warning: Unable to delete answers for {}".format(name))
        else:
            print("Error: Unable to prepare query to "
                  "delete answers for {}".format(name))
            return None
        if query.prepare(
                "DELETE FROM tests "
                "WHERE `Memory Set` == :name"):
            query.bindValue(":name", name)
            if not query.exec_():
                print("Warning: Unable to delete tests for {}".format(name))
        else:
            print("Error: Unable to prepare query to "
                  "delete tests for {}".format(name))
            return None

        return True

    def saveresults(self, name, results):
        query = QtSql.QSqlQuery(self.db)
        if query.prepare("INSERT INTO TESTS (`Memory Set`, "
                         "                   `TimeStamp`, "
                         "                   `Revision`) "
                         "SELECT r.`Memory Set`, "
                         "       DATETIME() AS TimeStamp, "
                         "       r.`Revision` "
                         "FROM memtableroot AS r "
                         "WHERE r.`Memory Set` == :name"):
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
