# Align columns - Gedit plugin
#
# Copyright (c) 2011 Hugo Henriques Maia Vieira
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

import gettext
import os

class Localization():
    """Provides a helper to easily setup l10n."""

    _initialized = False

    _domain = 'messages'
    _locale_path = os.path.join(os.path.dirname(__file__), 'locale')

    @classmethod
    def setup(cls):
        """Sets up the gettext localization."""

        if (not cls._initialized):
            gettext.install(cls._domain, cls._locale_path)
            cls._initialized = True

