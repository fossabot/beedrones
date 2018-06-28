'''
Created on Oct 27, 2016

Camundaintegration
@author: gd




'''
from logging import getLogger
import datetime
import base64
import ujson as json
from beecell.remote import(
    RemoteClient,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    MethodNotAllowedException,
    NotAcceptableException,
    ConflictException,
    ServerErrorException)
from urllib import urlencode
from beedrones.cloudstack.db_client.decorator import logger

# import urllib  #.request


class ApiConsumer(object):
    """
        ApiConsumer
    """
    pass


class WorkFlowEngine(object):
    """
        WorkFlowEngine
         a wrapper around Camunnda bpmn engine
    """
    # external task query parameters
    ext_task_queryitem = ('externalTaskId', 'topicName', 'workerId',
                          'locked', 'notLocked', 'withRetriesLeft',
                          'noRetriesLeft', 'activityId', 'executionId',
                          'processInstanceId', 'processDefinitionId',
                          'active', 'priorityHigherThanOrEquals',
                          'priorityLowerThanOrEquals', 'suspended',
                          'sortBy', 'sortOrder', 'firstResult',
                          'maxResults')

    def __init__(self, conn, user='anonymous', passwd='anonymous',
                 proxy=None, keyfile=None, certfile=None):
        """
            :param conn: Request connection. Ex. {'host':'10.102.160.12',
                                                'port':9090,
                                                'path':'/engine-rest',
                                                'proto':'http'}
            :param proxy: proxy server. Ex. ('proxy.it', 3128) [default=None]
            http:/10.102.160.12:9090/engine-rest/
        """
        #self.logger = getLogger('behive_bpm')
        self.logger = getLogger(self.__class__.__module__+ \
                                        '.'+self.__class__.__name__)          
        self.baseurl = ""
        self.connection = conn
        self.user = user
        self.password = passwd
        self.proxy = proxy

        self.client = RemoteClient(conn, user, passwd, proxy)
        self.baseheader = {
            'Authorization': 'Basic ' + base64.b64encode(user + ':' + passwd)
        }

        # list of class that define a service
        #self.service_classes = service_classes
        #self.service_classes.insert(0, Service)


    def process_deployment_create(
            self,
            source,
            name,
            checkduplicate=True,
            changeonly=True,
            tenantid=None):
        '''Create a deployment and the process definition inside it
        
            :param name: STRING The name for the deployment to be created.
            :param checkduplicate: BOOLEAN
            :param changeonly:
            :param source: text/plain
            :param tenantid:  str

            POST /deployment/create            
        '''
        import requests
        if checkduplicate:
            edf = 'true'
        else:
            edf = 'false'
        payload = [
            ('deployment-name', name),
            ('enable-duplicate-filtering', edf),
            ('deployment-source', 'beehive process application'),
            ('data', (name + '.bpmn', source))
        ]

        path = self.connection["proto"] + "://" + str(self.connection["host"]) + ":" + \
            str(self.connection["port"]) + \
            self.connection["path"] + '/deployment/create'

        r = requests.post(path, auth=(self.user, self.password), files=payload)
        r.raise_for_status()
        return r

    def process_deployment_delete(
            self,
            processDeploymentId,
            cascade=True,
            skipCustomListeners=False
            ):
        '''Delete a deployment
        
            :param cascade: BOOLEAN, true, if all process instances, historic process 
            instances and jobs for this deployment should be deleted.
            :param skipCustomListeners: BOOLEAN true, if only the built-in ExecutionListeners
            should be notified with the end event.

            DELETE /deployment/{id}
        '''
        query = {}
        query['cascade'] = cascade
        query['skipCustomListeners'] = skipCustomListeners
        path = '/deployment/%s'%processDeploymentId
        path = '%s?%s' % (path, urlencode(query)) 
        if cascade == True:
            processes = self.process_definition_get(deploymentId=processDeploymentId)
            #self.logger.info('Processes to be deleted ' + str(process_definition_list))            
            for process in processes:
                self.logger.info('Processes to be deleted type' + str(type(processes)))
                processDefinitionId = process['id']
                self.process_definition_delete(processDefinitionId=processDefinitionId, cascade=True, skipCustomListeners=True)
        #return  processDefinitionId
        return self.client.run_http_request2(path, 'DELETE')
        
        
        #         import requests
        #         path = self.connection["proto"] + "://" + str(self.connection["host"]) + ":" + \
        #             str(self.connection["port"]) + \
        #             self.connection["path"] + '/deployment/%s'%processDeploymentId
        #         path = '%s?%s' % (path, urlencode(query)) 
        #         r = requests.delete(path, auth=(self.user, self.password))
        #         r.raise_for_status()
        #         return r.json()

    def process_deployment_get(self,processDeploymentId=None):
        '''Create a deployment
        
            :param id: STRING depployment identifier

            GET /deployment/{id}
        '''

        if processDeploymentId == None:
            processDeploymentId=''
        path = self.baseurl + '/deployment/%s' %processDeploymentId
        return self.client.run_http_request2(path, 'GET')
        #         import requests
        #         path = self.connection["proto"] + "://" + str(self.connection["host"]) + ":" + \
        #             str(self.connection["port"]) + \
        #             self.connection["path"] + '/deployment/%s'%processDeploymentId
        #         r = requests.get(path, auth=(self.user, self.password))
        #         r.raise_for_status()
        #         return r.json()    
    
    def case_definition_get(self,processDeploymentId=None):
        '''Queries for case definitions that fulfill given parameters
        
            :param processDeploymentId: STRING depployment identifier

            GET /case-definition
        '''
        query={}
        query['deploymentId'] = processDeploymentId
        path = '/case-definition'
        path = '%s?%s' % (path, urlencode(query))  
        return self.client.run_http_request2(path, 'GET')
    
    def process_definition_xml_get(self, processDefinitionId=None, key=None, tenantId=None):
        '''Retrieves the BPMN 2.0 XML of a process definition.

            :param processDefinitionId STRING: process identifier
            :param key STRING: key the key identifier for the process we use the process key in order 
                to always use last revision of the project
            :param tenantId STRING: the tenant identifier
            Get XML
            GET /process-definition/{id}/xml
            GET /process-definition/key/{key}/xml
            GET /process-definition/key/{key}/tenant-id/{tenant-id}/xml
        '''
        if processDefinitionId == None:
            if key != None:
                if tenantId == None:
                    path = self.baseurl + '/process-definition/key/%s/xml' %key
                else:
                    path = self.baseurl + '/process-definition/key/%s/tenant-id/%s/xml'%(key,tenantId)
        else:
            path = self.baseurl + '/process-definition/%s/xml' %processDefinitionId
        return self.client.run_http_request2(path, 'GET')['bpmn20Xml']
    
    def process_definition_list(self):
        ''' Get the list of process definitions available
            Get List
            GET /process-definition
        '''
        path = self.baseurl + '/process-definition'
        return self.client.run_http_request2(path, 'GET')

    def process_definition_get(self, processDefinitionId=None, key=None, tenantId=None, deploymentId=None):
        '''Get a process definition filtering on params
        
            :param processDefinitionId STRING: process identifier
            :param key STRING: key the key identifier for the process we use the process key in order 
                to always use last revision of the project
            :param tenantId STRING: the tenant identifier
            :param deploymentId STRING: the deployment id 
            
            GET /process-definition/{id}
            GET /process-definition/key/{key}
             (returns the latest version of the process definition which belongs to no tenant)
            GET /process-definition/key/{key}/tenant-id/{tenant-id}
             (returns the latest version of the process definition for tenant)
        '''
        if processDefinitionId == None:
            if key != None:
                if tenantId == None:
                    path = self.baseurl + '/process-definition/key/' + key
                else:
                    path = self.baseurl + '/process-definition/key/%s/tenant-id/%s'%(key,tenantId)
            elif deploymentId != None:
                path = self.baseurl + '/process-definition?deploymentId=%s'%deploymentId
            else:
                path = self.baseurl + '/process-definition'
        else:
            path = self.baseurl + '/process-definition/%s'%processDefinitionId
        return self.client.run_http_request2(path, 'GET')

    def process_definition_delete(
            self,
            processDefinitionId,
            cascade=True,
            skipCustomListeners=True
            ):
        '''Delete a Process definition

            DELETE /process-definition/{id}
                    
            :param cascade: BOOLEAN, true, if all process instances, historic process 
            instances and jobs for this deployment should be deleted.
            :param skipCustomListeners: BOOLEAN true, if only the built-in ExecutionListeners
            should be notified with the end event.

        '''
        import requests
        query = {}
        query['cascade'] = cascade
        query['skipCustomListeners'] = skipCustomListeners
        path = self.connection["proto"] + "://" + str(self.connection["host"]) + ":" + \
            str(self.connection["port"]) + \
            self.connection["path"] + '/process-definition/%s'%processDefinitionId
        path = '%s?%s' % (path, urlencode(query)) 
        r = requests.delete(path, auth=(self.user, self.password))
        r.raise_for_status()
        return r

    def process_instance_start_processDefinitionId(self, processDefinitionId, businessKey=None, variables=None):
        """
        """
        return self.process_instance_start_processkey(processDefinitionId, businessKey=businessKey, variables=variables)

    def process_instance_start_processkey(self, key, businessKey=None, variables=None):
        '''Instantiates a given process definition. Process variables and business key may be supplied.
        
            :param processDefinitionId: the id of the process definition
            :param businessKey: the value for businessKey 
                The business key the process instance is to be initialized with.
                The business key uniquely identifies the process instance in 
                the context of the given process definition
            :param process_variables: a dict with the process variables
        '''
        if variables is None:
            variables = {}

        payload = self.variablesfrompyton(variables)
        if businessKey is not None:
            payload['businessKey'] = businessKey
        data = json.dumps(payload)

        return self.client.run_http_request2(
            '/process-definition/key/' + key + '/start', 'POST',
            data=data, headers={'Content-Type': 'application/json'})

    def process_instances_list(self, processDefinitionKey=None, businessKey=None, processInstanceIds=None):
        """Get running process instances
        
            POST /process-instance
            Authorization: Basic YWRtaW46YWRtaW5hZG1pbg==
            :param processInstanceIds: LIST or STRING,  a list of process instance or a single instance. 
            :param businessKey: STRING process instance business key.
            :param processDefinitionKey: STRING Filter by the key of the process definition the instances run on
                   attention: the key not the id.
        """
        att_filter = {}
        if processDefinitionKey is not None:
            att_filter['processDefinitionKey'] = processDefinitionKey
        if businessKey is not None:
            att_filter['businessKey'] = businessKey
        if processInstanceIds is not None:
            if isinstance(processInstanceIds, list):
                att_filter['processInstanceIds'] = processInstanceIds
            else:
                att_filter['processInstanceIds'] = (processInstanceIds,)
        if len(att_filter) == 0:
            return None
        data = json.encode(att_filter)
        return self.client.run_http_request2(
            '/process-instance', 'POST', data=data,
            headers={'Content-Type': 'application/json'})

    def process_instances_get_all(self):
        """
            GET http://10.102.160.12:9090/engine-rest/process-instance  HTTP/1.1
            Authorization: Basic YWRtaW46YWRtaW5hZG1pbg==
        """
        return self.client.run_http_request2('/process-instance', 'GET')

    def process_instance_history_detail(self, processInstanceId=None):
        """Get completed process instances
        
            GET /history/process-instance/{pprocessInstanceIds}
            Authorization: Basic YWRtaW46YWRtaW5hZG1pbg==
            :param processInstanceIds: LIST or STRING,  a list of process instance or a single instance. 

        """
        path = "/history/process-instance/%s"%processInstanceId
        return self.client.run_http_request2(
           path, 'GET')

    def process_instance_status(self, processInstanceId=None):
        """Get completed process instances
        
            GET /history/process-instance/{pprocessInstanceIds}
            Authorization: Basic YWRtaW46YWRtaW5hZG1pbg==
            :param processInstanceIds: LIST or STRING,  a list of process instance or a single instance. 

        """
        path = "/history/process-instance/%s"%processInstanceId
        return self.client.run_http_request2(
           path, 'GET')['state']

    def process_instances_group_delete(self,processInstanceIds, deleteReason):
        """Deletes multiple process instances asynchronously (batch).
        
            POST /process-instance/delete
            Authorization: Basic YWRtaW46YWRtaW5hZG1pbg==
            :param processInstanceIds: a list of process instance.
            :param deleteReason: STRING the delete reason.
            
            NOTE: Shoould be available in last Camunda version
             
        """
        import requests
        dicttoDelete = {}
        if deleteReason is not None:
            dicttoDelete['deleteReason'] = deleteReason
        if processInstanceIds is not None:
            if isinstance(processInstanceIds, list):
                dicttoDelete['processInstanceIds'] = processInstanceIds
            else:
                dicttoDelete['processInstanceIds'] = (processInstanceIds,)
        if len(dicttoDelete) == 0:
            return None
        data = json.dumps(dicttoDelete)
        res = self.client.run_http_request2(
            '/process-instance/delete', 'POST', data=data,
            headers={'Content-Type': 'application/json'})
        return res

    def process_instance_delete(self, processInstanceId):
        """Deletes single process instances synchronously.
        
            DELETE /process-instance/{processInstanceId}
            :param processInstanceId: STRING the proces instance id
            
        """
        try:
            path = self.baseurl + '/process-instance/' + \
                processInstanceId
            result = self.client.run_http_request2(path, 'DELETE')
        except Exception as ex:
            return False
        return True

    def process_instance_variables_list(self, processInstanceId):
        """
            Get List
            GET /process-instance/{id}/variables
            :param processInstanceId: the proces instance id
        """
        path = self.baseurl + '/process-instance/' + processInstanceId + '/variables'
        result = self.client.run_http_request2(path, 'GET')
        return self.variablestopyton({'variables': result})

    # Post (Binary)
    # POST /process-instance/{id}/variables/{varName}/data    

    def process_instance_variables_list_ex(self, processInstanceId):
        """ gets all variables for a  runing process """
        pvar = self.client.run_http_request2(
            '/execution/' + processInstanceId + '/localVariables', 'GET')
        if pvar is None:
            pvar = {}
        return self.variablestopyton({'variables': pvar})

    def process_instance_variable_get(self, processInstanceId, varName):
        """
            Get
            GET /process-instance/{id}/variables/{varName}
            :param processInstanceId: the proces instance id
            :param varName: the name of the avariable to get
            
        """
        path = self.baseurl + '/process-instance/' + \
            processInstanceId + '/variables/' + varName
        result = self.client.run_http_request2(path, 'GET')
        return result
        # self.variablestopyton({'variables':result})


    def process_instance_variable_file_upload(self, processInstanceId, varName, varContent):
        """Use only with files, with variables and dictionaries use update method
        
            Get (Binary)
            POST /process-instance/{id}/variables/{varName}/data
            contente is a string
            :param processInstanceId: the proces instance id
            :param varName: the name of the avariable to fill
            :param content: a file handler opened in binary mode "rb" or a string with the content
            
            (1) Post binary content of a byte array variable:

            POST /process-instance/aProcessInstanceId/variables/aVarName/data
            
            Request Body:
            
            ---OSQH1f8lzs83iXFHphqfIuitaQfNKFY74Y
            Content-Disposition: form-data; name="data"; filename="unspecified"
            Content-Type: application/octet-stream
            Content-Transfer-Encoding: binary
            
            <<Byte Stream ommitted>>
            ---OSQH1f8lzs83iXFHphqfIuitaQfNKFY74Y
            Content-Disposition: form-data; name="valueType"
            Content-Type: text/plain; charset=US-ASCII
            Content-Transfer-Encoding: 8bit
            
            Bytes
            ---OSQH1f8lzs83iXFHphqfIuitaQfNKFY74Y--
            
            (2) Post the JSON serialization of a Java Class (deprecated):
            
            POST /process-instance/aProcessInstanceId/variables/aVarName/data
            
            Request Body:
            
            ---OSQH1f8lzs83iXFHphqfIuitaQfNKFY74Y
            Content-Disposition: form-data; name="data"
            Content-Type: application/json; charset=US-ASCII
            Content-Transfer-Encoding: 8bit
            
            ["foo", "bar"]
            ---OSQH1f8lzs83iXFHphqfIuitaQfNKFY74Y
            Content-Disposition: form-data; name="type"
            Content-Type: text/plain; charset=US-ASCII
            Content-Transfer-Encoding: 8bit
            
            java.util.ArrayList<java.lang.Object>
            ---OSQH1f8lzs83iXFHphqfIuitaQfNKFY74Y--
            
            (3) Post a text file:
            
            POST /process-instance/aProcessInstanceId/variables/aVarName/data
            
            Request Body:
            
            ---OSQH1f8lzs83iXFHphqfIuitaQfNKFY74Y
            Content-Disposition: form-data; name="data"; filename="myFile.txt"
            Content-Type: text/plain; charset=US-ASCII
            Content-Transfer-Encoding: binary
            
            <<Byte Stream ommitted>>
            ---OSQH1f8lzs83iXFHphqfIuitaQfNKFY74Y
            Content-Disposition: form-data; name="valueType"
            Content-Type: text/plain; charset=US-ASCII
            Content-Transfer-Encoding: 8bit
            
            File
            ---OSQH1f8lzs83iXFHphqfIuitaQfNKFY74Y--
           
        """
        import requests
        payload = [
            ('data', (varName, varContent, 'application/octet-stream')),
            ("valueType", ('Bytes', 'text/plain; charset=US-ASCII'))
        ]

        path = self.connection["proto"] + "://" + str(self.connection["host"]) + ":" + \
            str(self.connection["port"]) + \
            self.connection["path"] + '/process-instance/' + \
            processInstanceId + '/variables/' + varName + '/data'

        r = requests.post(path, auth=(self.user, self.password), files=payload)
        return r.text

    '''def process_instance_variables_update_old(self, processInstanceId, variables=None, deletenames=None):
        """
            Modify
            POST /process-instance/{id}/variables
            :param variables: a dictionary containig the variables
            :param deletenames: an iterable containg the delete variable names
        """
        path = self.baseurl + '/process-instance/' + processInstanceId + '/variables'
        data = {}
        if isinstance(variables, dict):
            cvars = self.variablesfrompyton(variables)
            data['modifications'] = cvars['variables']
        if hasattr(deletenames, '__iter__'):
            data['deletions'] = [x for x in deletenames]
        result = self.client.run_http_request2(
            path, 'POST', data=data,
            headers={'Content-Type': 'application/json'})
        return result'''

    def process_instance_variables_update(self, processInstanceId, variables=None, deletenames=None):
        """
            Modify
            POST /process-instance/{id}/variables
            :param variables: a dictionary containig the variables
            :param deletenames: an iterable containg the delete variable names
        """
        path = self.baseurl + '/process-instance/' + processInstanceId + '/variables'
        data = {}
        
        if variables is None:
            variables = {}

        payload = self.variablesfrompyton(variables)        
        if isinstance(variables, dict):
            cvars = self.variablesfrompyton(variables)
            data['modifications'] = cvars['variables']
        if hasattr(deletenames, '__iter__'):
            data['deletions'] = [x for x in deletenames]
        data = json.encode(data)            
        result = self.client.run_http_request2(
            path, 'POST', data=data,
            headers={'Content-Type': 'application/json'})
        return result



    def process_instance_variable_set(self, processInstanceId, varName, varValue, varType=None, valueInfo={}):
        """Update a single variable to a value
        
            Update
            PUT /process-instance/{id}/variables/{varName}
            
            BODY:
            {
              "value" : "ab",
              "type" : "Object",
              "valueInfo" : {
                "objectTypeName": "com.example.MyObject",
                "serializationDataFormat": "application/xml"
              }
             } 
        """
        data = {"value" : varValue, "type": varType, "valueInfo":valueInfo}
               
        path = self.baseurl + '/process-instance/' + \
            processInstanceId + '/variables/' + varName
        data = json.encode(data)
        result = self.client.run_http_request2(
            path, 'PUT', data=data,
            headers={'Content-Type': 'application/json'})
        return result

    def process_instance_varariable_delete(self, processInstanceId, varName):
        """
            Delete
            DELETE /process-instance/{id}/variables/{varName}
            :param processInstanceId: the proces instance id
            :param varName: the name of the avariable to delete
            
        """
        try:
            path = self.baseurl + '/process-instance/' + \
                processInstanceId + '/variables/' + varName
            result = self.client.run_http_request2(path, 'DELETE')
        except Exception as ex:
            return False
        return True


    def tasks_list(self, att_filter=None):
        '''Quuery tasks
        
           :param att_filter a dicrtionary containing the key-value  to search
            
            {"id":"anId",
            "name":"aName",
            "assignee":"anAssignee",
            "created":"2013-01-23T13:42:42",
            "due":"2013-01-23T13:49:42",
            "followUp:":"2013-01-23T13:44:42",
            "delegationState":"RESOLVED",
            "description":"aDescription",
            "executionId":"anExecution",
            "owner":"anOwner",
            "parentTaskId":"aParentId",
            "priority":42,
            "processDefinitionId":"aProcDefId",
            "processInstanceId":"aProcInstId",
            "caseDefinitionId":"aCaseDefId",
            "caseInstanceId":"aCaseInstId",
            "caseExecutionId":"aCaseExecution",
            "taskDefinitionKey":"aTaskDefinitionKey",
            "formKey":"aFormKey",
            "tenantId":"aTenantId"}
        '''
        if att_filter is None:
            att_filter = {}

        # head = {'Content-Type': 'application/json'}

        data = json.encode(att_filter)
        return self.client.run_http_request2(
            '/task', 'POST', data=data,
            headers={'Content-Type': 'application/json'})

    def task_get(self, taskId=None):
        '''Query task
        
            GET /task/{id}
        
           :param taskId The id of the task to be retrieved.
        '''
        path = "/task/%s"%taskId
        return self.client.run_http_request2(
            path, 'GET')        

    def task_variables_get(self, taskId=None):
        '''
            get task variablee  tasks
            :param filter a dicrtionary cintaining the key value paure tio search

        '''
        path = '/task/' + taskId + '/variables'
        ret = self.client.run_http_request2(path, 'GET')
        return ret

    def task_complete(self, taskid, variables=None):
        '''
            :param processDefinitionId: the id aof the process
            :param process_variables: a dict with the process variables
        '''
        if variables is None:
            variables = {}
        variables = self.variablesfrompyton(variables)
        # head = {'Content-Type': 'application/json'}

        data = json.encode(variables)
        return self.client.run_http_request2(
            '/task/' + taskid + '/complete', 'POST', data=data,
            headers={'Content-Type': 'application/json'})

    '''
        Get Rendered Start Form
        GET /process-definition/{id}/rendered-form
        GET /process-definition/key/{key}/rendered-form
        GET /process-definition/key/{key}/tenant-id/{tenant-id}/rendered-form

        Get Start Form Key
        GET /process-definition/{id}/startForm
        GET /process-definition/key/{key}/startForm
        GET /process-definition/key/{key}/tenant-id/{tenant-id}/startForm
        Get Process Instance Statistics
        GET /process-definition/statistics


        Submit Start Form
        POST /process-definition/{id}/submit-form
        POST /process-definition/key/{key}/submit-form
        POST /process-definition/key/{key}/tenant-id/{tenant-id}/submit-form

        Activate/Suspend By Id
        PUT /process-definition/{id}/suspended
        PUT /process-definition/key/{key}/suspended
        PUT /process-definition/key/{key}/tenant-id/{tenant-id}/suspended
        Activate/Suspend By Key
        PUT /process-definition/suspended
    '''
    # proces instance Variables

    def batch_get(self, batchId=None):
        '''Quuery tasks
        
           :param batchId: STRING Filter by batch id.
            
        '''
        path = '/batch/'+batchId
        return self.client.run_http_request2(
            path, 'GET')

    @staticmethod
    def typefrompyton(val):
        """
            return the type definition for val
            :param val a object:
        """
        if isinstance(val, basestring): return "String"
        elif isinstance(val, bool): return "Boolean"
        elif isinstance(val, int): return "Integer"
        elif isinstance(val, long): return "Long"
        elif isinstance(val, float): return "Double"
        elif isinstance(val, datetime.date): return "Date"
        else:
            return "Object"

    @staticmethod
    def variablesfrompyton(pvars):
        """ 
            convert a dictionary into a camunda variables rappresentation
            @param pvars dict the dictionary containing variables
            see https://docs.camunda.org/manual/7.4/user-guide/process-engine/variables/
            camunda supported object are:
                boolean: Instances of java.lang.Boolean
                bytes: Instances of byte[]
                short: Instances of java.lang.Short
                integer: Instances of java.lang.Integer
                long: Instances of java.lang.Long
                double: Instances of java.lang.Double
                date: Instances of java.util.Date
                string: Instances of java.lang.String
                null: null references

                file
                object
                json
                xml
        """
        try:
            ret = {}
            for name in pvars:
                variable = {'value': pvars[name], 'type': None}
                if isinstance(pvars[name], basestring):
                    variable['type'] = "String"
                elif isinstance(pvars[name], bool):
                    variable['type'] = "Boolean"
                elif isinstance(pvars[name], int):
                    variable['type'] = "Integer"
                elif isinstance(pvars[name], long):
                    variable['type'] = "Long"
                elif isinstance(pvars[name], float):
                    variable['type'] = "Double"
                elif isinstance(pvars[name], datetime.date):
                    variable['type'] = "Date"
                ret[name] = variable
            pass
        except Exception as ex:
            logger = getLogger('behive_bpm')
            logger.error(ex)
        return {'variables': ret}

    @staticmethod
    def variablestopyton(variables):
        """ convert a dictionary into a camunda variables rappresentation
            see https://docs.camunda.org/manual/7.4/user-guide/process-engine/variables/
            camunda supported object are:
                boolean: Instances of java.lang.Boolean
                bytes: Instances of byte[]
                short: Instances of java.lang.Short
                integer: Instances of java.lang.Integer
                long: Instances of java.lang.Long
                double: Instances of java.lang.Double
                date: Instances of java.util.Date
                string: Instances of java.lang.String
                null: null references

                file
                object
                json
                xml
        """
        try:
            if not 'variables' in variables:
                ret = None
                raise Exception(
                    'variables not present in dictionary while converting to python')
            pvars = variables['variables']
            ret = {}
            for name in pvars:
                ret[name] = pvars[name]['value']
                vtype = pvars[name]['type']

                if vtype == "String":
                    ret[name] = str(ret[name])
                elif vtype == "Boolean":
                    ret[name] = bool(ret[name])
                elif vtype == "Long":
                    ret[name] = long(ret[name])
                elif vtype == "Short" or vtype == "Integer":
                    ret[name] = int(ret[name])
                elif vtype == "Double":
                    ret[name] = float(ret[name])
                elif vtype == "Date":
                    ret[name] = datetime.date(ret[name])
                elif vtype == "Null":
                    ret[name] = None
        except Exception as ex:
            logger = getLogger('behive_bpm')
            logger.error(ex)
            ret = None
        return ret

    def incidents(self):
        '''
            return the list of the incidents
                http://10.102.160.12:9090/engine-rest/incident
            Get List
            GET /incident
            Get List Count
            GET /incident/count
        '''
        pass
    # external task api

    def externaltask_get(self, taskid):
        """
            Get
            GET /external-task/{id}
            get external task
            |Name                |Value  |Description
            |activityId          |String |The id of the activity that this external task belongs to.
            |activityInstanceId  |String |The id of the activity instance that the external task belongs to.
            |errorMessage        |String |The error message that was supplied when the last failure of this task was reported.
            |executionId         |String |The id of the execution that the external task belongs to.
            |id                  |String |The id of the external task.
            |lockExpirationTime  |String |The date that the task's most recent lock expires or has expired.
            |processDefinitionId |String |The id of the process definition the external task is defined in.
            |processDefinitionKey|String |The key of the process definition the external task is defined in.
            |processInstanceId   |String |The id of the process instance the external task belongs to.
            |tenantId            |String |The id of the tenant the external task belongs to.
            |retries             |Number |The number of retries the task currently has left.
            |suspended           |Boolean|A flag indicating whether the external task is suspended or not.
            |workerId            |String |The id of the worker that posesses or posessed the most recent lock.
            |priority            |Number |The priority of the external task.
            |topicName           |String |The topic name of the external task.
        """
        path = self.baseurl + '/external-tasky/' + taskid
        task = self.client.run_http_request2(path, 'GET')
        return BpmnExternalTask(self, **task)

    def __ext_task_qry(self, path, **kwargs):
        """
            execute a query post
        """
        att_filter = {}
        for item in self.ext_task_queryitem:
            if item in kwargs:
                att_filter[item] = kwargs[item]
        # head = {'Content-Type': 'application/json'}

        data = json.encode(att_filter)
        result = self.client.run_http_request2(
            path, 'POST', data=data,
            headers={'Content-Type': 'application/json'})
        return result

    def externaltask_query(self, **kwargs):
        """
            Get List
            GET /external-task
            Get List (POST)
            POST /external-task
            Get List Count (POST)
            query external task
        """
        result = self.__ext_task_qry('/external-task', **kwargs)
        return [BpmnExternalTask(self, **res) for res in result]

    def externaltask_count(self, **kwargs):
        """
            Get List Count
            GET /external-task/count
            POST /external-task/count
        """
        result = self.__ext_task_qry('/external-task/count', **kwargs)
        if 'count' in result:
            return result['count']
        else:
            return 0

    def externaltask_fetch_and_lock(self, workerid, maxtasks, topicname,
                                    usepriority=True, lockduration=360000):
        """ 
            Fetch and Lock
            POST /external-task/fetchAndLock
        """
        att = {
            "workerId": workerid,
            "maxTasks": maxtasks,
            "usePriority": usepriority,
            "topics": [{"topicName": topicname,
                        "lockDuration": lockduration,
                        }]
        }
        # head = {'Content-Type': 'application/json'}

        data = json.encode(att)
        result = self.client.run_http_request2(
            '/external-task/fetchAndLock', 'POST', data=data,
            headers={'Content-Type': 'application/json'})
        return [BpmnExternalTask(self, workerid=workerid, **res) for res in result]

    def externaltask_complete(self, taskid, workerid, pvars=None):
        """
            Complete
            POST /external-task/{id}/complete
        """
        if pvars is not None:
            att = self.variablesfrompyton(pvars)
        else:
            att = {}
        att["workerId"] = workerid

        data = json.encode(att)
        url = '/external-task/%s/complete' % taskid
        self.client.run_http_request2(
            url, 'POST', data=data, headers={'Content-Type': 'application/json'})
        return True

    def externaltask_error(self, taskid, workerid, errorcode):
        """
            Handle BPMN Error
            POST /external-task/{id}/bpmnError
        """
        att = {
            "workerId": workerid,
            "errorCode": errorcode
        }
        data = json.encode(att)
        url = '/external-task/%s/bpmnError' % taskid
        self.client.run_http_request2(
            url, 'POST', data=data,
            headers={'Content-Type': 'application/json'})
        return True

    def externaltask_failure(self, taskid, workerid, errormsg, errordetail=None, retries=3, timeout=60000):
        """
            Handle Failure
            POST /external-task/{id}/failure
        """
        att = {
            "workerId": workerid,
            "errorMessage": "Does not compute",
            "retries": retries,
            "retryTimeout": timeout
        }
        if isinstance(errordetail, str):
            att['errorDetails'] = errordetail
        data = json.encode(att)
        url = '/external-task/%s/failure' % taskid
        self.client.run_http_request2(
            url, 'POST', data=data,
            headers={'Content-Type': 'application/json'})
        return True

    def externaltask_unlock(self, taskid):
        """
            Unlock
            POST /external-task/{id}/unlock
        """
        url = '/external-task/%s/unlock' % taskid
        self.client.run_http_request2(url, 'POST',)
        return True

    def externaltask_priority(self, taskid, priority):
        """
            Set Priority
            PUT /external-task/{id}/priority
        """
        data = '{"priority":%i}' % int(priority)
        url = '/external-task/%s/priority' % taskid
        self.client.run_http_request2(
            url, 'PUT', data=data,
            headers={'Content-Type': 'application/json'})
        return True

    def externaltask_retries(self, taskid, retries):
        """
            Set Retries
            PUT /external-task/{id}/retries
        """
        data = '{"retries":%i}' % int(retries)
        url = '/external-task/%s/retries' % taskid
        self.client.run_http_request2(
            url, 'PUT', data=data,
            headers={'Content-Type': 'application/json'})
        return True


class BpmnExternalTask (object):
    """
        BpmnExternalTask
        classe per  gestire task esterni per la costruzione 
        di un worker python per l'esecuzione di task
    """
    taskparameters = ('activityId', 'activityInstanceId',
                      'errorMessage', 'executionId', 'id',
                      'lockExpirationTime', 'processDefinitionId',
                      'processDefinitionKey', 'processInstanceId',
                      'tenantId', 'retries', 'suspended', 'workerId',
                      'priority', 'topicName', )

    def __init__(self, engine, workerid=None, **kwargs):
        """
            get external task
        """

        self.engine = engine
        self.definition = kwargs
        self._workerid = workerid
        self.locked = self._workerid is not None
        if self.locked:
            self.variables = WorkFlowEngine.variablestopyton(kwargs)
        else:
            self.variables = {}

    @property
    def taskid(self):
        if 'id' in self.definition:
            return self.definition['id']

    @property
    def workerid(self):
        if self.locked:
            return self._workerid
        elif 'workerId' in self.definition:
            return self.definition['id']
        else:
            return None

    def unlock(self):
        """ 
            unloack the task
        """
        return self.engine.externaltask_unlock(self.taskid)

    def fail(self, errormsg, errordetail=None, retries=3, timeout=60000):
        """
            tsak exwecution fails
        """
        return self.engine.externaltask_failure(self.taskid, self.workerid,
                                                errormsg, errordetail, retries, timeout)

    def set_variables(self, **kwargs):
        """
            update the process variables
        """
        if isinstance(kwargs, dict):
            self.variables.update(kwargs)

    def complete(self, **kwargs):
        """
            update the process variables
        """
        if isinstance(kwargs, dict):
            self.set_variables(**kwargs)
        self.engine.externaltask_complete(
            self.taskid, self.workerid, self.variables)

    @property
    def priority(self):
        if 'priority' in self.definition:
            return self.definition['priority']
        else:
            return None

    @priority.setter
    def priority(self, priority):
        """
            Set Priority
        """
        self.definition['priority'] = priority
        return self.engine.externaltask_priority(self.taskid, priority)

    @property
    def retries(self):
        if 'retries' in self.definition:
            return self.definition['retries']
        else:
            return None

    @retries.setter
    def retries(self, retries):
        """
            Set Retries
        """
        self.definition['retries'] = retries
        return self.engine.externaltask_retries(self.taskid, retries)

    def error(self, error):
        """
            set error msg on task
        """
        return self.engine.externaltask_error(self.taskid, self.workerid, str(error))
