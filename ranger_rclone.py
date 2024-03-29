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

import ranger.api
from ranger.api.commands import Command
from ranger.core.loader import CommandLoader
from ranger.core.shared import FileManagerAware
from os.path import isfile
import csv

class rclone_targets_obj(FileManagerAware):
    """Stores rclone_targets, writes them into a file in the ranger config
    directory, is initialized at startup below."""
    def __init__(self):
        self.targets_file = self.fm.confpath("rclone_targets")
        self.dictionary = dict()

        if isfile(self.targets_file):
            with open(self.targets_file, "r", newline='') as csvfile:
                targets_reader = csv.reader(csvfile, delimiter=',')
                self.dictionary = dict(targets_reader)

    def update_file(self):
        """writes rclone_targets.dictionary into file"""
        with open(self.targets_file,'w', newline='') as csvfile:
            targets_writer = csv.writer(csvfile, delimiter=',')
            targets_writer.writerows(self.dictionary.items())


# instantiate rclone_target
HOOK_INIT_OLD = ranger.api.hook_init
def hook_init(fm):
    fm.rclone_targets = rclone_targets_obj()
    return HOOK_INIT_OLD(fm)
ranger.api.hook_init = hook_init


class remove_rclone_target(Command):

    def execute(self):
        key = self.arg(1)

        if key in self.fm.rclone_targets.dictionary:
            self.fm.rclone_targets.dictionary.pop(key)
            self.fm.rclone_targets.update_file()
            self.fm.notify('Rclone target removed')
            return
        else:
            self.fm.notify('Rclone target does not exist', bad=True)
            return


class add_rclone_target(Command):

    def execute(self):
        key = self.arg(1)
        target = self.arg(2)

        if key == target:
            self.fm.notify('Keyword and Target are identical', bad=True)
            return
        elif key in self.fm.rclone_targets.dictionary:
            self.fm.notify('Keyword already exists', bad=True)
            return
        else:
            self.fm.rclone_targets.dictionary[key] = target
            self.fm.rclone_targets.update_file()
            self.fm.notify('Rclone target added')
            return


class change_rclone_target(Command):

    def execute(self):
        key = self.arg(1)
        target = self.arg(2)

        if key == target:
            self.fm.notify('Keyword and Target are identical', bad=True)
            return
        elif key not in self.fm.rclone_targets.dictionary:
            self.fm.notify('Keyword does not exist yet, use :add_rclone_target',
                           bad=True)
            return
        else:
            self.fm.rclone_targets.dictionary[key]=target
            self.fm.rclone_targets.update_file()
            self.fm.notify('Rclone target changed')
            return


class rclone(Command):

    command_list = ["copy", "copyto", "move", "moveto"]

    def execute(self):

        command = self.arg(1)
        files = self.fm.thisdir.get_selection()

        if self.arg(2) in self.fm.rclone_targets.dictionary:
            target = self.fm.rclone_targets.dictionary[self.arg(2)]
        else:
            target = self.arg(2)

        if self.arg(3):
            # This allows to copy the files into a subfolder of target, even
            # when using a bookmark.
            target = target + "/" + self.arg(3)

        if not command in self.command_list:
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
                                          "--no-traverse", "-q", file.path,
                                          target], descr=descr)
                self.fm.loader.add(obj)
        return

    def tab(self, tabnum):

        def match_fn(argnum, options):
            if self.arg(argnum):
                return filter(lambda x: (self.arg(argnum) in x), options)
            else:
                return options

        def complete_fn(argnum, options):
            return (self.start(argnum) + o for o in match_fn(argnum, options))

        if self.arg(1) in self.command_list:
            return complete_fn(2, self.fm.rclone_targets.dictionary)
        else:
            return complete_fn(1, self.command_list)
