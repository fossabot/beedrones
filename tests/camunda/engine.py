'''
Created on Mar 22, 2017

@author: darkbk, pas
'''
import gevent
from pyVim import connect
import json
import unittest
import random
import time
from beecell.simple import id_gen
from beedrones.camunda.engine import WorkFlowEngine
from tests.test_util import run_test, CloudapiTestCase
from time import sleep

conn = {
    'host': '10.102.160.12',
    'port': 9090,
    'path': '/engine-rest',
    'proto': 'http'
}

USER = 'admin'
#USER = 'pippo'
PASSWD = 'adminadmin'
WFTEST = None

class WorkFlowEngineTestCase(CloudapiTestCase):
    """To execute this test you need a cloudstack instance.
    """
    def setUp(self):
        CloudapiTestCase.setUp(self)
        
    def intialize(self):
        global WFTEST
        if WFTEST is None:
            WFTEST = WorkFlowEngine(conn, user=USER, passwd=PASSWD)        
        
    def load_config_file(self, filename):
        """
        """
        f = open(filename, 'r')
        config = f.read()
        f.close()
        return config.rstrip()
        
    #
    # deployment
    #
    def test_wf_process_list(self):
        '''
            returns all the running process_definition_list
        '''
        self.intialize()
        res = WFTEST.process_definition_list()
        self.logger.info(self.pp.pformat(res))
        
    def test_wf_process_filtered(self):
        '''
            returns a single process_definition_get (the last version) with the given ID filtering with processDefinitionId, 
            process_definition_get key, tenantId 
        '''
        self.intialize()
        processDefinitionId = u'Checkmail_simple:1:3adc6768-2107-11e7-beff-061b3800031f'
        res = WFTEST.process_definition_get(processDefinitionId)
        self.logger.info(self.pp.pformat(res))
        res = WFTEST.process_definition_get(key=u'invoice', tenantId=None)
        self.logger.info(self.pp.pformat(res))         
        res = WFTEST.process_definition_get(deploymentId=u'3ad95a25-2107-11e7-beff-061b3800031f')
        self.logger.info(self.pp.pformat(res))         

            
        
    def test_wf_xmlget_filtered(self):
        '''
            returns the last xml version of a process_definition_get, filtering with processDefinitionId, 
            process_definition_get key, tenantId 
        '''
        self.intialize()
        key = u'invoice'
    
        res = WFTEST.process_definition_xml_get(key=key)
        self.logger.info(res)
  
        
    def test_wf_xmlpost(self):
        '''
            Create a new deployment
        '''
        global WFTEST
        self.intialize()
        
        xml = self.load_config_file(u'./prova.xml')
        
        res = WFTEST.process_deployment_create(xml, u'Checkmail_simple')
        self.logger.info(self.pp.pformat(res))

    def test_wf_get_deployment(self):
        '''
            delete a deployment
        '''
        global WFTEST
        self.intialize()
       
        res = WFTEST.process_deployment_get()
        #res = WFTEST.process_deployment_get('080d882b-1554-11e7-a173-061b3800031f')
        self.logger.info(self.pp.pformat(res))

    def test_wf_delete_deployment(self):
        '''
            delete a deployment
        '''
        global WFTEST
        self.intialize()
        
        res = WFTEST.process_deployment_delete('3ad95a25-2107-11e7-beff-061b3800031f')
        self.logger.info(self.pp.pformat(res))

    def test_wf_case_definition_get(self):
        '''
            get a case def
        '''
        global WFTEST
        self.intialize()
        
        #res = WFTEST.case_definition_get()
        res = WFTEST.case_definition_get()
        self.logger.info(self.pp.pformat(res))

    def test_wf_startproc(self):
        global WFTEST
        self.intialize()
        #res = WFTEST.process_definition_xml_get('test_approvazione')
        amount = 1000.0 * random.random()
        # parameters= {
        #     "variables": {
        #         "amount": {
        #             "value": amount,
        #             "type": "double"
        #         },
        #         "invoiceCategory": {
        #             "value": "pippo--" + str(amount),
        #             "type": "string"
        #         }
        #     }
        # }
        parameters = {
            "Random": amount,
            "VariableString": "pippo--" + str(amount),
            "Dictionary":{"key1":"val1","key2":"val2"}
        }
        res = WFTEST.process_instance_start_processDefinitionId('Checkmail_simple', businessKey='',
                                  variables=parameters)
        self.logger.info(self.pp.pformat(res))

    def test_wf_delete_process_definition(self):
        '''
            delete a process_definition_get definition
        '''
        global WFTEST
        self.intialize()
       
        res = WFTEST.process_definition_delete('Checkmail_simple:1:fdff6255-20f8-11e7-beff-061b3800031f')
        self.logger.info(self.pp.pformat(res))

    def test_wf_process_all_instances(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instances_get_all()
        self.logger.info(self.pp.pformat(res))

    def test_wf_process_instance(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instances_list(processDefinitionKey=u'Checkmail_simple')
        self.logger.info(self.pp.pformat(res))
        #         res = WFTEST.process_instances_list(businessKey=u'9cb55b4ec272205c8b30')
        #         self.logger.info(self.pp.pformat(res))
        #res = WFTEST.process_instances_list(processInstanceIds=u'a4eaac77-259f-11e7-b663-061b3800031f')
        #self.logger.info(self.pp.pformat(res))

    def test_wf_get_history_instances(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_history_detail(processInstanceId=u'9f69862a-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res))

    def test_wf_verify_process_instance_status(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_status(processInstanceId=u'9f69862a-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res))


    def test_wf_process_instances_delete(self):
        global WFTEST
        self.intialize()
        listProc = [u'c24626fa-1525-11e7-a173-061b3800031f',u'8426fbf4-1525-11e7-a173-061b3800031f']
        res = WFTEST.process_instances_group_delete(processInstanceIds=listProc,deleteReason=u'this is the reason')
        self.logger.info(self.pp.pformat(res))
        sleep(5)
        res = WFTEST.process_instances_list(processInstanceIds=listProc)
        self.logger.info(self.pp.pformat(res))
     
    def test_wf_process_single_instance_delete(self):
        global WFTEST
        self.intialize()
        processInstanceId= u'd39e596f-1526-11e7-a173-061b3800031f'
        res = WFTEST.process_instance_delete(processInstanceId)
        self.logger.info(self.pp.pformat(res))
        
    def test_wf_process_instance_get_variables(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_variables_list(processInstanceId=u'938f021d-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res)) 
    
    def test_wf_process_instance_get_variables_ex(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_variables_list_ex(processInstanceId=u'938f021d-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res)) 

    def test_wf_process_instance_get_single_variable(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_variable_get(processInstanceId=u'938f021d-259f-11e7-b663-061b3800031f', varName=u'VariableString')
        self.logger.info(self.pp.pformat(res)) 
        
    def test_wf_process_instance_upload_variable(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_variable_file_upload(processInstanceId=u'938f021d-259f-11e7-b663-061b3800031f', 
                                            varName=u'Variable_2', varContent=u'POEPROEPROEPROEP')
        self.logger.info(self.pp.pformat(res))         

    def test_wf_process_instance_update_variables(self):
        global WFTEST
        self.intialize()
        parameters = {
            "VariableString_2": "POEPROEPROEPROEP",
            "VariableString":{"prova":"val"}
        }        
        res = WFTEST.process_instance_variables_update(processInstanceId=u'938f021d-259f-11e7-b663-061b3800031f', 
                                                     variables=parameters)
        self.logger.info(self.pp.pformat(res))      

    def test_wf_process_instance_set_variable(self):
        global WFTEST
        self.intialize()
        #         res = WFTEST.process_instance_variable_set(processInstanceId=u'938f021d-259f-11e7-b663-061b3800031f',
        #                                             varName='VariableString_2', 
        #                                             varValue='nmnmnmnmnmm', 
        #                                             varType='String', 
        #                                             valueInfo={})
        res = WFTEST.process_instance_variable_set(processInstanceId=u'938f021d-259f-11e7-b663-061b3800031f',
                                            varName='VariableString_2', 
                                            varValue={"prova":"val"}, 
                                            valueInfo={
                                            })        
        self.logger.info(self.pp.pformat(res))

    def test_wf_process_instance_delete_variable(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_varariable_delete(processInstanceId=u'938f021d-259f-11e7-b663-061b3800031f',
                                            varName='VariableString_2')        
        self.logger.info(self.pp.pformat(res))        

    def test_wf_tasks_using_asignee(self):
        global WFTEST
        self.intialize()
        fi = {'assignee': 'demo'}
        #res = WFTEST.tasks_list(fi)
        res = WFTEST.tasks_list()
        self.logger.info(self.pp.pformat(res))
        
    def test_wf_tasks_using_process_name(self):
        global WFTEST
        self.intialize()
        fi = {'processInstanceId': '9f69862a-259f-11e7-b663-061b3800031f',
              'name':'verify'}
        #res = WFTEST.tasks_list(fi)
        res = WFTEST.tasks_list(fi)
        self.logger.info(self.pp.pformat(res))
        
    def test_wf_get_task_id(self):
        global WFTEST
        self.intialize()
        res = WFTEST.task_get(taskId=u'a9f1719f-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res))                  

    def test_wf_get_task_varibles(self):
        global WFTEST
        self.intialize()
        res = WFTEST.task_variables_get(taskId=u'a9f1719f-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res)) 
        

    def test_wf_complete_task(self):
        global WFTEST
        self.intialize()        
        res = WFTEST.task_complete(u'a476dc02-259f-11e7-b663-061b3800031f', {'settvar': True})
        self.logger.info(self.pp.pformat(res)) 
                  
        
    def test_wf_get_batch(self):      
        global WFTEST
        self.intialize()
        res = WFTEST.batch_get(u'c4ca0e16-2053-11e7-9a5c-061b3800031f')
        self.logger.info(self.pp.pformat(res))
        
def test_suite():
    tests = [
        # system
        
        #---------- DEPLOYMENT------------        
        #u'test_wf_xmlpost',       
        #u'test_wf_get_deployment'
        #u'test_wf_delete_deployment', 
        
        #-----------CASE DEFINITION-------
        #u'test_wf_case_definition_get'
                  
        #-----------PROCESSES-------------
        #u'test_wf_process_list',
        #u'test_wf_process_filtered',
        #u'test_wf_xmlget',
        #u'test_wf_startproc',
        #u'test_wf_delete_process_definition'
        
        #--------PROCESS INSTANCES--------
        #u'test_wf_process_all_instances',
        #u'test_wf_process_instance',
        #u'test_wf_process_instances_delete',
        #u'test_wf_process_single_instance_delete',
        #u'test_wf_get_history_instances',
        #u'test_wf_verify_process_instance_status',
        
        #----------VARIABLES--------------
        u'test_wf_process_instance_get_variables',
        u'test_wf_process_instance_get_variables_ex',
        #u'test_wf_process_instance_get_single_variable',
        #u'test_wf_process_instance_upload_variable' NOT USED
        #u'test_wf_process_instance_update_variables',
        #u'test_wf_process_instance_set_variable',
        #u'test_wf_process_instance_delete_variable',
        
        #-------------TASKS---------------
        #u'test_wf_tasks_using_asignee',
        #u'test_wf_tasks_using_process_name',
        #u'test_wf_get_task_id',
        #u'test_wf_get_task_varibles',
        #u'test_wf_complete_task',   
        
        #-------------BATCHS--------------
        #u'test_wf_get_batch'
                
    ]
    return unittest.TestSuite(map(WorkFlowEngineTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])