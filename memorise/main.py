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

from memorise import Memorise, datastore, icon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from pathlib import Path
import sys
import os.path

def main():
    app = QApplication(sys.argv)

    icon_dir = os.path.dirname(icon.__file__)
    app_icon = QIcon()
    for size in [70, 144, 150, 310]:
        app_icon.addFile('{0}/icon-{1}x{1}.png'.format(icon_dir, size),
                         QSize(size, size))
    app.setWindowIcon(app_icon)

    #TODO: consider windows path
    dbfile = str(Path.home().joinpath(".pymem.db"))

    with datastore.Datastore(dbfile) as ds:
        m = Memorise(datastore=ds)
        m.show()
        app.exec_()

if __name__ == "__main__":
    main()
