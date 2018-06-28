'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import os
import pprint
from gibbon_cloud.cloudstack.api_pxroxy.base import ProxyApi, ProxyError
from gibbon_utility.perf import watch_test 

def suite_ProxyApi():
    tests = ['test_send_api_request',
            ]
    return unittest.TestSuite(map(ProxyApiTestCase, tests))

class ProxyApiTestCase(unittest.TestCase):
    logger = logging.getLogger('test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
        from tests.gibbon_cloud.config import params
        base_url = params['gibbon_cloud.cloudstack.dso']['base_url']
        api_key = params['gibbon_cloud.cloudstack.dso']['api_key']
        sec_key = params['gibbon_cloud.cloudstack.dso']['sec_key']
        self.pp = pprint.PrettyPrinter()
        
        from flask import Flask
        from flask import request
        app = Flask(__name__)
        app.debug = True

        with app.test_request_context('/hello', method='POST', args=[]):
            # now you can do something with the request until the
            # end of the with block, such as basic assertions:
            print request.path
            print request.method
        
    def tearDown(self):
        pass

    @watch_test
    def test_send_api_request(self):
        try:
            params = {'command':'listRegions'}
            res = self.server.send_api_request(params)
            self.logger.debug(res)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)