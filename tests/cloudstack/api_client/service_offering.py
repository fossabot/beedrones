'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import time
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.api_client import ServiceOffering, Orchestrator
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class ServiceOfferingCase(CloudTestCase):
    """Template api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object. [optional]
    :type data: dict or None
    :param oid: set oid for current object. [optional]
    :type data: str or None    
    """      
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()

        offeringid = 'ec3cce76-2330-444c-89fc-4fda2b37fbaf'
        self.offering = ServiceOffering(self.api_client, oid=offeringid)
        self.offering.extend(self.db_session, self.hypervisors)
        
        self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        self.system.extend(self.db_session, self.hypervisors)
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    def test_info(self):
        res = self.offering.info()
    
    def test_create_update_delete_offering(self):
        name = 'offering-%s' % random.randint(0, 10000)
        cpunumber = 1
        cpuspeed = 1000
        memory = 1024
        res = self.system.create_service_offerings(name, name, cpunumber, 
                                                   cpuspeed, memory)
        offering = ServiceOffering(self.api_client, oid=res['id'])
        res = offering.update(name+'_update', name)
        res = offering.delete()

def test_suite():
    tests = [
             'test_info',
             'test_create_update_delete_offering',
            ]
    return unittest.TestSuite(map(ServiceOfferingCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])