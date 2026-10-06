# -*- coding: utf-8 -*-

import logging
import os
import threading
import uuid

from distutils.util import strtobool

import openerp.http as http

_logger = logging.getLogger(__name__)

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None  # noqa
    _logger.debug("Cannot 'import pythonjsonlogger'.")


def is_true(strval):
    return bool(strtobool(strval or '0'.lower()))


class OdooJsonFormatter(jsonlogger.JsonFormatter):

    def add_fields(self, log_record, record, message_dict):
        record.pid = os.getpid()
        record.dbname = getattr(threading.currentThread(), 'dbname', '?')
        record.request_id = getattr(threading.currentThread(), 'request_uuid', None)
        record.perf_info = getattr(record, 'perf_info', '')
        if record.perf_info:
            nb_queries, time_sql, time_python = record.perf_info.split()
            time_sql = float(time_sql)
            time_python = float(time_python)
            time_total = time_sql + time_python
            record.perf_info_nb_queries = int(nb_queries)
            record.perf_info_time_sql = time_sql
            record.perf_info_time_python = time_python
            record.perf_info_time_total = time_total

        _super = super(OdooJsonFormatter, self)
        return _super.add_fields(log_record, record, message_dict)


if is_true(os.environ.get('ODOO_LOGGING_JSON')):
    format = ('%(asctime)s %(pid)s %(levelname)s'
              '%(dbname)s %(request_id)s %(name)s: %(message)s %(perf_info)s')
    formatter = OdooJsonFormatter(format)
    logging.getLogger().handlers[0].formatter = formatter


_original_webrequest_init = http.WebRequest.__init__


def new_webrequest_init(self, httprequest):
    _original_webrequest_init(self, httprequest)
    threading.currentThread().request_uuid = uuid.uuid4().hex


http.WebRequest.__init__ = new_webrequest_init
