# Copyright (c) 2013 Dale Sedivec
# Copyright (c) 2016 Cody Opel <codyopel@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from beets import library, util
from beets.plugins import BeetsPlugin
from logging import getLogger
from os import listdir, path
from shutil import move, Error

log = getLogger('beets')

class MoveAllPlugin (BeetsPlugin):
    """movall plugin for beets"""

    def __init__(self):
        super(MoveAllPlugin, self).__init__()
        self.config.add({
            'exclude_files': [ ],
            'exclude_exts': [ ],
        })
        self.register_listener('item_moved', handle_item_moved)
        self.register_listener('cli_exit', handle_cli_exit)


MULTIPLE_DESTS = object()
directories_moved = {}


def handle_item_moved(source, destination, **_kwargs):
    global directories_moved

    src_dir = path.dirname(source)
    existing_dst_dir = directories_moved.get(src_dir)

    if existing_dst_dir is MULTIPLE_DESTS:
        return

    dst_dir = path.dirname(destination)

    if existing_dst_dir:
        if not path.samefile(dst_dir, existing_dst_dir):
            directories_moved[src_dir] = MULTIPLE_DESTS
    elif not path.samefile(src_dir, dst_dir):
        directories_moved[src_dir] = dst_dir


def handle_cli_exit(lib, **_kwargs):
    for src_dir, dst_dir in directories_moved.items():
        if dst_dir is MULTIPLE_DESTS:
            print("moves out of %s have multiple dests, will not moveall" %
                  (src_dir,))
            continue

        remaining_items = lib.items(library.PathQuery('path', src_dir))

        if next(iter(remaining_items), None):
            print("moveall: some Beets items left in %s, will not move" % (src_dir,))
        elif path.exists(src_dir):
            print("moveall: moving all leftovers in %s to %s" % (src_dir, dst_dir))
            for remaining_item in listdir(src_dir):
                remaining_item_path = path.join(src_dir, remaining_item).decode('utf8')
                destination_path = dst_dir.decode('utf8')

                try:
                    move(remaining_item_path, destination_path)
                except Error, ex:
                    log.critical("failed to move {0} to {1}: {2}", dirent_path,
                                 dst_dir, ex)

            util.prune_dirs(src_dir)
