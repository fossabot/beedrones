'''
Created on Dec 14, 2015

@author: darkbk
'''
import gevent
from tests.test_util import run_test, CloudapiTestCase
from pyVim import connect
#from beedrones.vsphere.client import VsphereManager
from beedrones.veeam.client import VeeamManager, VeeamJob, VeeamClient
from xmltodict import parse as xmltodict


import json
import unittest
import random
import time
#from pyVmomi import vim

contid = 14
component = u'NSX'






class VsphereUtilTestCase(CloudapiTestCase):
    """To execute this test you need a cloudstack instance.
    """
    def setUp(self):
        CloudapiTestCase.setUp(self)
        
        jobsBackup = {
            'Backup_VSPHERE':'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/4e15202b-ffd4-473e-b4dc-9a5128c89d35',
            'Backup_by_API':'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b',
            'Backup_testusr':'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312',
            'Backup_Estemporaneo':'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
            
            }
        
        '''
        Job presenti sul test:
        Nome 
            Backup_VSPHERE 
            --> 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/4e15202b-ffd4-473e-b4dc-9a5128c89d35'
            Backup_by_API
            --> 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
            Backup_testusr
            --> 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312'
            Backup_Estemporaneo
            --> 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
            
        
        '''
 
         
        '''
        veeamTest = {'host':'tst-veeamsrv.tstsddc.csi.it', 'port':'9399',
                 'user':'Administrator',
                 'pwd':'cs1$topix', 'verified':False}

        veeamProd = {'host':'veeambackup.csi.it', 'port':'9399',
                 'user':'localcloud',
                 'pwd':'Serverdmz$2016!', 'verified':False}
        '''
        veeamTest = {'uri':'http://tst-veeamsrv.tstsddc.csi.it:9399',
                 'user':'Administrator',
                 'pwd':'cs1$topix', 'verified':False}
        
        veeamProd = {'uri':'http://veeambackup.csi.it:9399',
                 'user':'160610555',
                 'pwd':'Admin$201606', 'verified':False}

        veeamProd = {'uri':'http://veeambackup.csi.it:9399',
                 'user':'160610555',
                 'pwd':'Admin$201606', 'verified':False}
         
        
        
        #self.client=VeeamClient("http://tst-veeamsrv.tstsddc.csi.it:9399")        
        #self.util=VeeamManager(veeamTest)
        self.util=VeeamManager(veeamTest)
        #self.jobs=VeeamJob(self.util,self.client)
        

        
        #self.util = VsphereManager(vcenter, nsx)
        
    def tearDown(self):
        CloudapiTestCase.tearDown(self)
 
    '''   
    def wait_task(self, task):
        while task.info.state not in [vim.TaskInfo.State.success,
                                      vim.TaskInfo.State.error]:
            self.logger.info(task.info.state)
            gevent.sleep(1)
            
        if task.info.state in [vim.TaskInfo.State.error]:
            self.logger.info("Error: %s" % task.info.error.msg)
        if task.info.state in [vim.TaskInfo.State.success]:
            self.logger.info("Completed")            
    '''    
    def test_veeam_connection(self):
        res = self.util.ping_veeam()  
        self.assertTrue(res)      
        self.logger.info(res)

    def test_veeam_call(self):
        #base_path="tst-veeamsrv.tstsddc.csi.it:9399"
        method='GET'
        #path='/api/query?type=job&filter=name==Backup_testusr'
        path='http://tst-veeamsrv.tstsddc.csi.it:9399/api/tasks'
        #path='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312?format=Entity'

        #token=self.util.veeam_token        
        
        
        res=self.util.client.call(path, method,'','', 30, self.util.veeam_token , '')
        self.logger.info(res)
           
    def test_get_tasks(self):
        res=self.util.get_tasks()
        self.assertTrue(res['status']=='OK')

    def test_get_task_props(self):
        taskId='task-70'
        res=self.util.get_task_props(taskId)
        self.assertTrue(res['status']=='OK')


    def test_get_jobs(self):
        res=self.util.jobs.get_jobs()
        self.assertTrue(res['status']=='OK')
        #self.logger.debug(res)
        
    def test_get_job_props(self):
        path='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312?action=edit'
        res=self.util.jobs.get_job_props(path)
        self.assertTrue(res['status']=='OK')
                    
    def test_edit_job(self):
        
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312?action=edit'

        XML="""<?xml version="1.0" encoding="utf-8"?>
        <Job Type="Job"  
        xmlns="http://www.veeam.com/ent/v1.0" 
        xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <JobScheduleOptions>
            <RetryOptions>
                <RetryTimes>3</RetryTimes>
                <RetryTimeout>5</RetryTimeout>
                <RetrySpecified>true</RetrySpecified>
            </RetryOptions>        
            <OptionsDaily Enabled="true">
                <Kind>Everyday</Kind>
                <Days>Sunday</Days>
                <Days>Monday</Days>
                <Days>Tuesday</Days>
                <Days>Wednesday</Days>
                <Days>Thursday</Days>
                <Days>Friday</Days>
                <Days>Saturday</Days>
                <Time>22:00:00.0000000</Time>
            </OptionsDaily>        
        </JobScheduleOptions>
        </Job>"""
        
        res=self.util.jobs.edit_job(href,XML)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')
    
    def test_start_job(self):
        #href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312'
        res=self.util.jobs.start_job(href)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')

    def test_stop_job(self):
        #href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312'
        res=self.util.jobs.stop_job(href)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')

    def test_retry_job(self):
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        res=self.util.jobs.retry_job(href)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')
        
    def test_clone_job(self):
        
        XML="""<?xml version="1.0" encoding="utf-8"?>
        <JobCloneSpec xmlns="http://www.veeam.com/ent/v1.0" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> 
        <BackupJobCloneInfo> <JobName>Prova Cloned Job</JobName> <FolderName>Prova Cloned Job</FolderName> 
        <RepositoryUid>urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca
        </RepositoryUid> </BackupJobCloneInfo> </JobCloneSpec>"""
        # "urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca"
        #XML='<?xml version="1.0" encoding="utf-8"'
        
        
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        
        
        res=self.util.jobs.clone_job(href,XML)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')
       
    def test_togglescheduleenabled_job(self):
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/029aa907-b538-4a68-8186-a7cf9033a4e3'
        res=self.util.jobs.togglescheduleenabled_job(href)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')
        
    def test_objsinjob_get_includes(self):
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312'
        res=self.util.jobobjs.get_includes(href)
        self.assertTrue(res['status']=='OK')
        #self.logger.debug(res)
    def test_objsinjob_props(self):
        href = 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312/includes/4e20ffc5-8382-4ab3-b6c1-7b956889fec8'
        res=self.util.jobobjs.get_includes_props(href)
        self.assertTrue(res['status']=='OK')
    
    def test_objsinjob_add(self):
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312'
        
        XML="""<?xml version="1.0" encoding="utf-8"?>
            <CreateObjectInJobSpec xmlns="http://www.veeam.com/ent/v1.0"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <HierarchyObjRef>urn:VMware:Vm:7f6b6270-1f3b-4dc6-872f-2d1dfc519c00.vm-1401</HierarchyObjRef>
            <HierarchyObjName>tst-calamari</HierarchyObjName>
            </CreateObjectInJobSpec>
            """
        
        #"urn:VMware:Vm:7f6b6270-1f3b-4dc6-872f-2d1dfc519c00.vm-1401'), (u'Name', u'tst-calamari')"
        
        
        res=self.util.jobobjs.add_includes(href,XML)
        self.assertTrue(res['status']=='OK')
        #self.logger.debug(res)

    def test_objsinjob_delete(self):
        href = 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312/includes/4e20ffc5-8382-4ab3-b6c1-7b956889fec8'
        res=self.util.jobobjs.delete_includes(href)
        self.assertTrue(res['status']=='OK')



def test_suite():
    tests = [
             # system
             #'test_veeam_call', 
             #'test_get_tasks',            
             #'test_get_task_props', 
             # Jobs
             'test_get_jobs',
             #'test_get_job_props',
             #'test_edit_job',
             #'test_start_job',
             #'test_stop_job',
             #'test_retry_job',
             #'test_clone_job',
             #'test_togglescheduleenabled_job',
             
             # Job Includes ( objs in job )
             #'test_objsinjob_get_includes',
             #'test_objsinjob_add',
             #'test_objsinjob_props',
             #'test_objsinjob_delete',
             


  
            ]
    return unittest.TestSuite(map(VsphereUtilTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])
    