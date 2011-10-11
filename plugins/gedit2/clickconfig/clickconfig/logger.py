#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  logger module
#
#  Copyright (C) 2010 Derek Veit
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
2010-06-18

This just wraps some of the standard logging module functionality for
the way I like to use it.

All messages are just sent to stdout, but it can be modified otherwise.
See http://docs.python.org/library/logging.html#useful-handlers
"""

DEFAULT_LOGGING_LEVEL = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')[0]

import datetime
import logging
import os
import sys

class Logger(object):
    """
    This class provides a log function.
    
    Usage in any given module:
        from logger import Logger
        LOGGER = Logger()
        
        LOGGER.log()
        LOGGER.log('Log this message')
        LOGGER.log('Log this message', level='error')
        LOGGER.log(var='var_name')
    
    """
    
    def __init__(self, level=DEFAULT_LOGGING_LEVEL):
        """Set up logging (to stdout)."""
        filename = sys._getframe(1).f_code.co_filename
        timestamp = str(datetime.datetime.now())
        logger_id = filename + timestamp
        self.logger = logging.getLogger(logger_id)
        handler = logging.StreamHandler(sys.stdout)
        log_format = "%(levelname)s - %(message)s"
        #log_format = "%(asctime)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        logging_level = getattr(logging, level)
        self.logger.setLevel(logging_level)
        self.log(('Logging started for %s' % filename).ljust(72, '-'))
    
    def log(self, message=None, level='info', var=None):
        """Log the message or log the calling function."""
        if message:
            logger = {'debug': self.logger.debug,
                      'info': self.logger.info,
                      'warning': self.logger.warning,
                      'error': self.logger.error,
                      'critical': self.logger.critical}[level]
            logger(message)
        elif var:
            self.logger.debug('%s: %r' % (var, sys._getframe(1).f_locals[var]))
        else:
            self.logger.debug(whoami())

def whoami():
    """Identify the calling function for logging."""
    filename = os.path.basename(sys._getframe(2).f_code.co_filename)
    line = sys._getframe(2).f_lineno
    if 'self' in sys._getframe(2).f_locals:
        class_name = sys._getframe(2).f_locals['self'].__class__.__name__
    else:
        class_name = '(No class)'
    function_name = sys._getframe(2).f_code.co_name
    return '%s Line %s %s.%s' % (filename, line, class_name, function_name)

def test():
    """Execute logger.py at the command line to run this self test."""
    test_var = [1, 'a']
    for logger_level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
        print('\nTesting for level: %s' % logger_level)
        LOGGER = Logger(level=logger_level)
        LOGGER.log('Log this message')
        LOGGER.log(var='test_var')
        LOGGER.log()
        for level in ('debug', 'info', 'warning', 'error', 'critical'):
            LOGGER.log('Log this %s message' % level, level=level)

if __name__ == '__main__':
    test()

