#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vi:ts=4:et

import unittest
import pycurl
import tempfile
import shutil
import functools
import os.path

from . import appmanager
from . import util

setup_module, teardown_module = appmanager.setup(('app', 8380))

def with_real_write_file(fn):
    @functools.wraps(fn)
    def wrapper(*args):
        with tempfile.NamedTemporaryFile() as f:
            with open(f.name, 'w+') as real_f:
                return fn(*(list(args) + [real_f]))
    return wrapper

class Acceptor(object):
    def __init__(self):
        self.buffer = ''

    def write(self, chunk):
        self.buffer += chunk.decode()

class WriteTest(unittest.TestCase):
    def setUp(self):
        self.curl = util.DefaultCurl()

    def tearDown(self):
        self.curl.close()

    def test_write_to_tempfile_via_function(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        f = tempfile.NamedTemporaryFile()
        try:
            self.curl.setopt(pycurl.WRITEFUNCTION, f.write)
            self.curl.perform()
            f.seek(0)
            body = f.read()
        finally:
            f.close()
        self.assertEqual('success', body.decode())

    def test_write_to_tempfile_via_object(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        f = tempfile.NamedTemporaryFile()
        try:
            self.curl.setopt(pycurl.WRITEDATA, f)
            self.curl.perform()
            f.seek(0)
            body = f.read()
        finally:
            f.close()
        self.assertEqual('success', body.decode())

    def test_write_to_file_via_function(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        dir = tempfile.mkdtemp()
        try:
            path = os.path.join(dir, 'pycurltest')
            f = open(path, 'wb+')
            try:
                self.curl.setopt(pycurl.WRITEFUNCTION, f.write)
                self.curl.perform()
                f.seek(0)
                body = f.read()
            finally:
                f.close()
        finally:
            shutil.rmtree(dir)
        self.assertEqual('success', body.decode())

    def test_write_to_file_via_object(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        dir = tempfile.mkdtemp()
        try:
            path = os.path.join(dir, 'pycurltest')
            f = open(path, 'wb+')
            try:
                self.curl.setopt(pycurl.WRITEDATA, f)
                self.curl.perform()
                f.seek(0)
                body = f.read()
            finally:
                f.close()
        finally:
            shutil.rmtree(dir)
        self.assertEqual('success', body.decode())

    def test_write_to_file_like(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        acceptor = Acceptor()
        self.curl.setopt(pycurl.WRITEDATA, acceptor)
        self.curl.perform()
        self.assertEqual('success', acceptor.buffer)
    
    @with_real_write_file
    def test_write_to_file_like_then_real_file(self, real_f):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        acceptor = Acceptor()
        self.curl.setopt(pycurl.WRITEDATA, acceptor)
        self.curl.perform()
        self.assertEqual('success', acceptor.buffer)

        self.curl.setopt(pycurl.WRITEDATA, real_f)
        self.curl.perform()
        real_f.seek(0)
        body = real_f.read()
        self.assertEqual('success', body.decode())

    def test_headerfunction_and_writefunction(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        header_acceptor = Acceptor()
        body_acceptor = Acceptor()
        self.curl.setopt(pycurl.HEADERFUNCTION, header_acceptor.write)
        self.curl.setopt(pycurl.WRITEFUNCTION, body_acceptor.write)
        self.curl.perform()
        self.assertEqual('success', body_acceptor.buffer)
        self.assertIn('content-type', header_acceptor.buffer.lower())

    def test_writeheader_and_writedata_file_like(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        header_acceptor = Acceptor()
        body_acceptor = Acceptor()
        self.curl.setopt(pycurl.WRITEHEADER, header_acceptor)
        self.curl.setopt(pycurl.WRITEDATA, body_acceptor)
        self.curl.perform()
        self.assertEqual('success', body_acceptor.buffer)
        self.assertIn('content-type', header_acceptor.buffer.lower())

    @with_real_write_file
    @with_real_write_file
    def test_writeheader_and_writedata_real_file(self, real_f_header, real_f_data):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        self.curl.setopt(pycurl.WRITEHEADER, real_f_header)
        self.curl.setopt(pycurl.WRITEDATA, real_f_data)
        self.curl.perform()
        real_f_header.seek(0)
        real_f_data.seek(0)
        self.assertEqual('success', real_f_data.read())
        self.assertIn('content-type', real_f_header.read().lower())

    def test_writedata_and_writefunction_file_like(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        data_acceptor = Acceptor()
        function_acceptor = Acceptor()
        self.curl.setopt(pycurl.WRITEDATA, data_acceptor)
        self.curl.setopt(pycurl.WRITEFUNCTION, function_acceptor.write)
        self.curl.perform()
        self.assertEqual('', data_acceptor.buffer)
        self.assertEqual('success', function_acceptor.buffer)

    @with_real_write_file
    def test_writedata_and_writefunction_real_file(self, real_f):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        function_acceptor = Acceptor()
        self.curl.setopt(pycurl.WRITEDATA, real_f)
        self.curl.setopt(pycurl.WRITEFUNCTION, function_acceptor.write)
        self.curl.perform()
        real_f.seek(0)
        self.assertEqual('', real_f.read().lower())
        self.assertEqual('success', function_acceptor.buffer)

    def test_writefunction_and_writedata_file_like(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        data_acceptor = Acceptor()
        function_acceptor = Acceptor()
        self.curl.setopt(pycurl.WRITEFUNCTION, function_acceptor.write)
        self.curl.setopt(pycurl.WRITEDATA, data_acceptor)
        self.curl.perform()
        self.assertEqual('success', data_acceptor.buffer)
        self.assertEqual('', function_acceptor.buffer)

    @with_real_write_file
    def test_writefunction_and_writedata_real_file(self, real_f):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        function_acceptor = Acceptor()
        self.curl.setopt(pycurl.WRITEFUNCTION, function_acceptor.write)
        self.curl.setopt(pycurl.WRITEDATA, real_f)
        self.curl.perform()
        real_f.seek(0)
        self.assertEqual('success', real_f.read().lower())
        self.assertEqual('', function_acceptor.buffer)

    def test_writeheader_and_headerfunction_file_like(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        data_acceptor = Acceptor()
        function_acceptor = Acceptor()
        body_acceptor = Acceptor()
        self.curl.setopt(pycurl.WRITEHEADER, data_acceptor)
        self.curl.setopt(pycurl.HEADERFUNCTION, function_acceptor.write)
        # silence output
        self.curl.setopt(pycurl.WRITEDATA, body_acceptor)
        self.curl.perform()
        self.assertEqual('', data_acceptor.buffer)
        self.assertIn('content-type', function_acceptor.buffer.lower())

    @with_real_write_file
    def test_writeheader_and_headerfunction_real_file(self, real_f):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        function_acceptor = Acceptor()
        body_acceptor = Acceptor()
        self.curl.setopt(pycurl.WRITEHEADER, real_f)
        self.curl.setopt(pycurl.HEADERFUNCTION, function_acceptor.write)
        # silence output
        self.curl.setopt(pycurl.WRITEDATA, body_acceptor)
        self.curl.perform()
        real_f.seek(0)
        self.assertEqual('', real_f.read().lower())
        self.assertIn('content-type', function_acceptor.buffer.lower())

    def test_headerfunction_and_writeheader_file_like(self):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        data_acceptor = Acceptor()
        function_acceptor = Acceptor()
        body_acceptor = Acceptor()
        self.curl.setopt(pycurl.HEADERFUNCTION, function_acceptor.write)
        self.curl.setopt(pycurl.WRITEHEADER, data_acceptor)
        # silence output
        self.curl.setopt(pycurl.WRITEDATA, body_acceptor)
        self.curl.perform()
        self.assertIn('content-type', data_acceptor.buffer.lower())
        self.assertEqual('', function_acceptor.buffer)

    @with_real_write_file
    def test_headerfunction_and_writeheader_real_file(self, real_f):
        self.curl.setopt(pycurl.URL, 'http://localhost:8380/success')
        function_acceptor = Acceptor()
        body_acceptor = Acceptor()
        self.curl.setopt(pycurl.HEADERFUNCTION, function_acceptor.write)
        self.curl.setopt(pycurl.WRITEHEADER, real_f)
        # silence output
        self.curl.setopt(pycurl.WRITEDATA, body_acceptor)
        self.curl.perform()
        real_f.seek(0)
        self.assertIn('content-type', real_f.read().lower())
        self.assertEqual('', function_acceptor.buffer)
