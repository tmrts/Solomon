# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-

from contextlib import contextmanager

@contextmanager
def suppress(*exceptions):
    """Suppress exceptions gracefully instead of using try/catch/pass"""
    try:
        yield
    except exceptions:
        pass

