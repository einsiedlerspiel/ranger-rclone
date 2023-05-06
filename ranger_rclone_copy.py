# Copyright 2022 Lou Woell.

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.

# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.

from ranger.api.commands import Command
from ranger.core.loader import CommandLoader
from ranger.core.shared import FileManagerAware
from os.path import isfile
import csv

class rclone_targets(FileManagerAware):
    """Stores rclone_targets, writes them into a file in the ranger config
    directory, is initialized at startup below."""
    def __init__(self):
        self.targets_file = self.fm.confpath("rclone_targets")
        self.targets = list()

        if isfile(self.targets_file):
            with open(self.targets_file, "r", newline='') as csvfile:
                targets_reader = csv.reader(csvfile, delimiter=',')
                for row in targets_reader:
                    self.targets.append(row)


    def list_targets(self):
        """returns list of key target pairs"""
        return self.targets


    def list_keys(self):
        """returns list of only the keys of all targets"""
        keylist = list()
        for x in self.targets:
            keylist.append(x[0])
        return keylist


    def add(self, key, target):
        """adds key target pair to rclone_targets"""
        self.targets.append([key, target])


    def get(self, key):
        """returns target to a given key"""
        if key:
            for row in self.targets:
                if key in row[0]:
                    return(row[1])
                return key
        else:
            return False



    def remove(self, key):
        """removes key target pair for a given key from rclone_targets"""
        for row in self.targets:
            if row[0] == key:
                self.targets.remove(row)
                return True
        return False


    def update_file(self):
        """writes rclone_targets into file"""
        with open(self.targets_file,'w', newline='') as csvfile:
            targets_writer = csv.writer(csvfile, delimiter=',')
            targets_writer.writerows(self.targets)


# instantiate rclone_target
rclone_target = rclone_targets()


class remove_rclone_target(Command):

    def execute(self):
        key = self.arg(1)

        if rclone_target.remove(key):
            rclone_target.update_file()
            self.fm.notify('Rclone target removed')
        else:
            self.fm.notify('Rclone target does not exist', bad=True)


class add_rclone_target(Command):

    def execute(self):
        key = self.arg(1)
        target = self.arg(2)

        if key == target:
            self.fm.notify('Keyword and Target are identical', bad=True)
            return
        elif rclone_target.get(key) != key:
            self.fm.notify('Keyword already exists', bad=True)
            return
        else:
            rclone_target.add(key, target)
            rclone_target.update_file()
            self.fm.notify('Rclone target added')


class change_rclone_target(Command):

    def execute(self):
        key = self.arg(1)
        target = self.arg(2)

        if key == target:
            self.fm.notify('Keyword and Target are identical', bad=True)
            return
        else:
            rclone_target.remove(key)
            rclone_target.add(key, target)

            rclone_target.update_file()
            self.fm.notify('Rclone target changed')


class rclone(Command):


    def execute(self):

        command_list = ["copy", "copyto", "move", "moveto"]
        command = self.arg(1)
        files = self.fm.thisdir.get_selection()
        target = rclone_target.get(self.arg(2))

        if not command in command_list:
            self.fm.notify("Missing command argument", bad=True)
            return
        elif not target:
            self.fm.notify('Missing target argument', bad=True)
            return
        elif not files:
            self.fm.notify('No files to copy', bad=True)
            return
        else:
            for file in files:
                descr = "rclone " + command + file.path + " to " + target
                obj = CommandLoader(args=["rclone", command,
                                          "--no-traverse", file.path,
                                          target], descr=descr)
                self.fm.loader.add(obj)
        return


    def tab(self, tabnum):
        return ["rclone" + " " +
                self.arg(1) + " " +
                target for target in rclone_target.list_keys()]
