'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.api_client import Domain, Orchestrator
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class DomainTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        # <domain id=ae3fad3c-d518-11e3-8225-0050560203f1, name=ROOT>
        # <domain id=4217b591-ae1e-4c83-8666-178966c6603a, name=domain-4909>
        # <domain id=3ee46212-cd07-4430-8c6f-51bc67cc7faf, name=CSI>
        # <domain id=b07b93ba-e402-42bf-8a5c-d9542f41be2a, name=PRG-EUROPEI>
        domainid = 'ae3fad3c-d518-11e3-8225-0050560203f1'
        self.domain = Domain(self.api_client, oid=domainid)
        
        self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        self.system.extend(self.db_session, self.hypervisors)        
        
    def tearDown(self):
        pass

    @watch_test
    def test_info(self):
        res = self.domain.info()

    @watch_test
    def test_tree(self):
        res = self.domain.tree()

    @watch_test
    def test_create_delete_domain(self):
        name = 'domain-%s' % random.randint(0, 10000)
        # create
        res = self.system.create_domain(name)
        # delete
        domain = Domain(self.api_client, oid=res._id)
        clsk_job_id = domain.delete()
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)        

    @watch_test
    def test_list_accounts(self):
        res = self.domain.list_accounts()

    @watch_test
    def test_list_create_delete_account(self):
        name = 'account-%s' % random.randint(0, 10000)
        type = 'USER'
        firstname = name
        lastname = name
        username = name
        password = name
        # create
        email = "%s@localhost.localdomain" % name
        account = self.domain.create_account(name, type, firstname, 
                                             lastname, username, password,
                                             email, timezone='CET')
        # list
        res = self.domain.list_accounts()
        for item in res:
            self.logger.debug(item)
        # remove
        clsk_job_id = self.domain.delete_account(account.id)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

def test_suite():
    tests = [
             'test_info',
             'test_tree',
             'test_list_accounts',
             'test_list_create_delete_account',
             'test_create_delete_domain',
            ]
    return unittest.TestSuite(map(DomainTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])