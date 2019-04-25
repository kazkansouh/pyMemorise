#! /bin/python3

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

import memorise
from memorise import Memorise, datastore, icon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, QCommandLineParser, QCommandLineOption
from pathlib import Path
import sys
import os.path

def process_args(app):
    args = {}

    parser = QCommandLineParser()
    parser.setApplicationDescription(
        ('PyMemorise is a tool to help memorise tables of data.' +
         ' It was built as an exam revision aid.'))
    parser.addHelpOption()
    parser.addVersionOption()

    dbOption = QCommandLineOption(
        ["database-file", "d"],
        "path to database, will be created if does not exist",
        "db",
        str(Path.home().joinpath(".pymem.db")))
    parser.addOption(dbOption)

    parser.process(app)

    args["database"] = parser.value(dbOption)

    if parser.positionalArguments():
        print(parser.positionalArguments())
        parser.showHelp()

    return args

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(memorise.name)
    app.setApplicationVersion(memorise.version)

    args = process_args(app)

    icon_dir = os.path.dirname(icon.__file__)
    app_icon = QIcon()
    for size in [70, 144, 150, 310]:
        app_icon.addFile('{0}/icon-{1}x{1}.png'.format(icon_dir, size),
                         QSize(size, size))
    app.setWindowIcon(app_icon)

    with datastore.Datastore(args['database']) as ds:
        m = Memorise(datastore=ds)
        m.show()
        app.exec_()

if __name__ == "__main__":
    main()
