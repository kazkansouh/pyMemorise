#! /bin/python3

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

from memorise import Memorise, datastore
from PyQt5.QtWidgets import QApplication
from pathlib import Path
import sys

def main():
    app = QApplication(sys.argv)

    #TODO: consider windows path
    dbfile = str(Path.home().joinpath(".pymem.db"))

    with datastore.Datastore(dbfile) as ds:
        m = Memorise(datastore=ds)
        m.show()
        app.exec_()

if __name__ == "__main__":
    main()
