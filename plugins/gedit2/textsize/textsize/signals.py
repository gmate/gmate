# -*- coding: utf-8 -*-
#
#  signals.py - Multi Edit
#
#  Copyright (C) 2009 - Jesse van den Kieboom
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330,
#  Boston, MA 02111-1307, USA.

class Signals:
    def __init__(self):
        self._signals = {}

    def _connect(self, obj, name, handler, connector):
        ret = self._signals.setdefault(obj, {})

        hid = connector(name, handler)
        ret.setdefault(name, []).append(hid)

        return hid

    def connect_signal(self, obj, name, handler):
        return self._connect(obj, name, handler, obj.connect)

    def connect_signal_after(self, obj, name, handler):
        return self._connect(obj, name, handler, obj.connect_after)

    def disconnect_signals(self, obj):
        if not obj in self._signals:
            return False

        for name in self._signals[obj]:
            for hid in self._signals[obj][name]:
                obj.disconnect(hid)

        del self._signals[obj]
        return True

    def block_signal(self, obj, name):
        if not obj in self._signals:
            return False

        if not name in self._signals[obj]:
            return False

        for hid in self._signals[obj][name]:
            obj.handler_block(hid)

        return True

    def unblock_signal(self, obj, name):
        if not obj in self._signals:
            return False

        if not name in self._signals[obj]:
            return False

        for hid in self._signals[obj][name]:
            obj.handler_unblock(hid)

        return True

    def disconnect_signal(self, obj, name):
        if not obj in self._signals:
            return False

        if not name in self._signals[obj]:
            return False

        for hid in self._signals[obj][name]:
            obj.disconnect(hid)

        del self._signals[obj][name]

        if len(self._signals[obj]) == 0:
            del self._signals[obj]

        return True

# ex:ts=4:et:
