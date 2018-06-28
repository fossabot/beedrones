'''
Created on Mar 17, 2016

@author: pas
'''
import ujson as json
from logging import getLogger
from beecell.simple import truncate
from urllib import urlencode, urlopen
from beedrones.openstack.client import OpenstackClient, OpenstackError

class OpenstackHeat(object):
    """Openstack Heat client
    
    Object to manage the openstack heat orchestrator
    
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                        '.'+self.__class__.__name__)        
        
        self.manager = manager
        self.uri = manager.endpoint('heat')
        self.client = OpenstackClient(self.uri, manager.proxy)

    def api(self):
        """Get compute api versions.
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        redux_uri = self.uri.split('/')[0]+"//"+self.uri.split('/')[2]
        client = OpenstackClient(redux_uri, self.manager.proxy)
        path = '/'
        self.logger.debug('Path to check: %s%s' % (client.path,path))
        res = client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack heat api: %s' % truncate(res))
        return res

    def stacks_list(self, ext_id=None, status=None, name=None, tenant=None, username=None,
             owner_id=None, limit=None, marker=None, show_deleted=False, 
             show_nested=False, sort_keys=None, tags=None, tags_any=None, 
             not_tags=None, not_tags_any=None, sort_dir=None, 
             global_tenant=True, with_count=False):
        """GET the Stack List
        
        :param ext_id: [optional] Filters the stack list by a stack ID. Use this 
                 filter multiple times to filter by multiple IDs. 
        :param status: [optional] Filters the stack list by a status. Use this 
                 filter multiple times to filter by multiple statuses. 
        :param name: [optional] Filters the stack list by a name. Use this
                 filter multiple times to filter by multiple names. NOTE: this
                 is the stack_name in the response.
        :param tenant: [optional] Filters the stack list by a tenant. Use this 
                 filter multiple times to filter by multiple tenants. 
                 NOTE: --- this param doesn't work without global_tenant.
        :param username: [optional] Filters the stack list by a user name. Use 
                 this filter multiple times to filter by multiple user names.
                 NOTE: it's the stack owner in the response, it's not possible 
                 to show stacks belonging to another owner different from the
                 one of the tenant. 
        :param owner_id: [optional] Filters the stack list by an owner ID, which 
                 is the ID of the parent stack of listed stack. Use this filter 
                 multiple times to filter by multiple owner IDs. 
        :param limit: [optional] Requests a page size of items. Returns a number
                 of items up to a limit value. Use the limit parameter to make 
                 an initial limited request and use the ID of the last-seen item
                 from the response as the marker parameter value in a subsequent
                 limited request.
        :param marker: [optional] The ID of the last-seen item. Use the limit 
                 parameter to make an initial limited request and use the ID of 
                 the last-seen item from the response as the marker parameter 
                 value in a subsequent limited request. Details (same in Neutron):
                 http://specs.openstack.org/openstack/neutron-specs/specs/api \
                 /networking_general_api_information.html                 
        :param show_deleted: [optional] Set to True to include deleted stacks in
                 the list. Default is False, which excludes deleted stacks from 
                 the list. 
        :param show_nested: [optional] Set to True to include nested stacks in 
                 the list.Default is False, which excludes nested stacks from 
                 the list. 
        :param sort_keys: [optional] Sorts the stack list by stack_name, 
                 stack_status, creation_time, or updated_time key. 
        :param tags: [optional] Lists stacks that contain one or more simple 
                 string tags. To specify multiple tags, separate the tags with 
                 commas. For example, tag1,tag2. The boolean AND expression is 
                 used to combine multiple tags. 
        :param tags_any: [optional] Lists stacks that contain one or more simple
                 string tags. To specify multiple tags, separate the tags with 
                 commas. For example, tag1,tag2. The boolean OR expression is 
                 used to combine multiple tags. 
        :param not_tags: [optional] Lists stacks that do not contain one or more 
                 simple string tags. To specify multiple tags, separate the tags 
                 with commas. For example, tag1,tag2. The boolean AND expression 
                 is used to combine multiple tags. 
        :param not_tags_any: [optional] Lists stacks that do not contain one or 
                 more simple string tags. To specify multiple tags, separate the 
                 tags with commas. For example, tag1,tag2. The boolean OR 
                 expression is used to combine multiple tags. 
        :param sort_dir: [optional] The sort direction of the list. A valid 
                 value is asc (ascending) or desc (descending). 
        :param global_tenant: [optional] Set to True to include stacks from all 
                 tenants in the stack list. Specify policy requirements in the 
                 Orchestration policy.json file. Default is False. 
        :param with_count: [optional] Set to True to include a count key in the 
                 response. The count key value is the number of stacks that
                 match the query criteria. Default is False.  NOTE: the count
                 works only without other filters. 
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        query = {}
        path = '/stacks'
        if ext_id is not None:
            query['id'] = ext_id
        if name is not None:
            query['name'] = name
        if status is not None:
            query['status'] = status
        if tenant is not None:
            query['tenant'] = tenant
        if username is not None:
            query['username'] = username
        if owner_id is not None:
            query['owner_id'] = owner_id
        if limit is not None:
            query['limit'] = limit
            query['marker'] = marker
        if show_deleted is True:
            query['show_deleted'] = 'TRUE'
        if show_nested is True:
            query['show_nested'] = 'TRUE'
        if sort_keys is not None:
            query['sort_keys'] = sort_keys
        if tags is not None:
            query['tags'] = tags
        if tags_any is not None:
            query['tags_any'] = tags_any
        if not_tags is not None:
            query['not_tags'] = not_tags
        if not_tags_any is not None:
            query['not_tags_any'] = not_tags_any
        if sort_dir is not None:
            query['sort_dir'] = sort_dir
        if global_tenant is True:
            query['global_tenant'] = 'TRUE'
        if with_count is True:
            query['with_count'] = 'TRUE'
                
        path = '%s?%s' % (path, urlencode(query))           
        
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        if with_count is True:
            self.logger.debug('Get openstack heat stacks count: %s' % \
                              truncate(res[0]['count']))
            return res[0]['count']
        self.logger.debug('Get openstack heat stack: %s' % \
                          truncate(res[0]))
        if 'stacks' in res[0]:
            return res[0]['stacks']
        else:
            return None
        
    def stacks_create(self, stack_name, template_url=None, template=None, 
               environment=None, files=None, parameters=None, tags=None,
               timeout_mins=None, disable_rollback=True, use_all_urls=False):
        """Create stack
        
        :param stack_name: A name for the new stack. This value must be unique 
            within a project. The name must start with an ASCII letter and can 
            contain ASCII letters, digits, underscores, periods, and hyphens. 
            When you delete or abandon a stack, its name 
            will not become available for reuse until the deletion completes 
            successfully.
        :param template_url: [optional] A URI to the location containing the
            stack template on which to perform the operation. See the
            description of the template parameter for information about the
            expected template content located at the URI. This parameter is
            only required when you omit the template parameter. If you
            specify both parameters, this parameter is ignored. 
        :param template: The stack template on which to perform the operation.
            This parameter is always provided as a string in the JSON request
            body. The content of the string is a JSON- or YAML-formatted
            Orchestration template. For example:
            
            .. code-block:: python    
            
                "template": {
                    "heat_template_version": "2013-05-23",
                    ...
                } 
            
            This parameter is required only when you omit the template_url
            parameter. If you specify both parameters, this value overrides
            the template_url parameter value. 
        :param environment: [optional] A JSON environment for the stack. 
        :param files: [optional] Supplies the contents of files referenced in
            the template or the environment. Stack templates and resource
            templates can explicitly reference files by using the get_file
            intrinsic function. In addition, the environment parameter can
            contain implicit references to files. 
            The value is a JSON object, where each key is a relative or
            absolute URI which serves as the name of a file, and the
            associated value provides the contents of the file. The following
            code shows the general structure of this parameter.
            
            .. code-block:: python    
            
                { 
                    ...,
                    "files": {
                        "fileA.yaml": "Contents of the file",
                        "file:///usr/fileB.template": "Contents of the file",
                        "http://example.com/fileC.template": "Contents of the file"
                    },
                    ...
                } 
            
            Additionally, some template authors encode their user data in a
            local file. The Orchestration client examines the template for
            the get_file intrinsic function and adds an entry to the files
            map with the path to the file as the name and the file contents
            as the value. 
            Do not use this parameter to provide the content of the template
            located at the template_url address. Instead, use the template
            parameter to supply the template content as part of the request. 
        :param parameters: [optional] Supplies arguments for parameters
            defined in the stack template. 
            The value is a JSON object, where each key is the name of a
            parameter defined in the template and the associated value is the
            argument to use for that parameter when instantiating the
            template. The following code shows the general structure of this
            parameter. In the example, a and b would be the names of two
            parameters defined in the template. 
            
            .. code-block:: python    
            
                {   
                    ...,
                    "parameters": {
                        "a": "Value",
                        "b": "3"
                    },
                    ...
                } 
            
            While the service accepts JSON numbers for parameters with the
            type number and JSON objects for parameters with the type json,
            all parameter values are converted to their string representation
            for storage in the created Stack. Clients are encouraged to send
            all parameter values using their string representation for
            consistency between requests and responses from the Orchestration
            service. 
            A value must be provided for each template parameter which does
            not specify a default value. However, this parameter is not
            allowed to contain JSON properties with names that do not match a
            parameter defined in the template. 
            The files parameter maps logical file names to file contents.
            Both the get_file intrinsic function and provider template
            functionality use this mapping. When you want to use a provider
            template, for example, the Orchestration service adds an entry to
            the files map by using: 
            The URL of the provider template as the name. 
            The contents of that file as the value. 
            Additionally, some template authors encode their user data in a
            local file. The Orchestration client examines the template for
            the get_file intrinsic function and adds an entry to the files
            map with the path to the file as the name and the file contents
            as the value. So, a simple example looks like this: 
            
            .. code-block:: python            
            
                {
                    "files": {
                        "myfile": "...."
                    },
                    ...,
                    "stack_name": "teststack",
                    "template": {
                        ...,
                        "resources": {
                            "my_server": {
                                "type": "OS::Nova::Server",
                                "properties": {
                                    ...,
                                    "user_data": {
                                        "get_file": "myfile"
                                    }
                                }
                            }
                        }
                    },
                    "timeout_mins": 60
                } 
            
        :param tags: [optional] One or more simple string tags to associate
            with the stack. To associate multiple tags with a stack, separate
            the tags with commas. For example, tag1,tag2. 
        :param timeout_mins: [optional] The timeout for stack creation in
            minutes. 
        :param disable_rollback: [optional] Enables or disables deletion of
            all previously-created stack resources when stack creation fails.
            Set to True to keep all previously-created stack resources when
            stack creation fails. Set to False to delete all
            previously-created stack resources when stack creation fails.
            Default is True.
        :param use_all_urls: [optional] Default False. Must be True if you 
            need to pass other params as files in a URL 
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: stcck id and stack links:
        
        .. code-block:: python
           
            {
                "stack": {
                    "id": "3095aefc-09fb-4bc7-b1f0-f21a304e864c",
                    "links": [
                        {
                            "href": "http://192.168.123.200:8004/v1/eb1c63a\
                            4f77141548385f113a28f0f52/stacks/teststack/3095\
                            aefc-09fb-4bc7-b1f0-f21a304e864c",
                            "rel": "self"
                        }
                    ]
                }
            }        
        """
        
        data={}
        data['stack_name']=stack_name
        
        if template is not None:
            data['template'] = template
        if template_url is not None:
            data['template_url'] = template_url
        if environment is not None:
            if use_all_urls is True:
                environment=json.loads(urlopen(environment).read())
            data['environment'] = json.loads(environment)    
        if parameters is not None:
            if use_all_urls is True:
                parameters=json.loads(urlopen(parameters).read())
            data['parameters'] = json.loads(parameters)
        if timeout_mins is not None:
            data['timeout_mins'] = timeout_mins
        if files is not None:
            if use_all_urls is True:
                files=json.loads(urlopen(files).read())
            data['files'] = json.loads(files)
        if tags is not None:
            data['tags'] = tags            
        if disable_rollback is False:
            data['disable_rollback'] = 'FALSE'
        elif disable_rollback is True:
            data['disable_rollback'] = 'TRUE'
        #print data
        path = '/stacks'
        res = self.client.call(path, 'POST', token=self.manager.identity.token,
                               data=json.dumps(data))
        self.logger.debug('Create openstack heat stack: %s' % truncate(res))
        return res[0]

    def stacks_preview(self, stack_name, template_url=None, template=None, 
               environment=None, files=None, parameters=None, tags=None,
               timeout_mins=None, disable_rollback=True, use_all_urls=False):
        """ Previews a stack.
        
        :param Same params present in create module.  
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: all stack       
        """
        
        data={}
        data['stack_name']=stack_name
        
        if template is not None:
            data['template'] = template
        if template_url is not None:
            data['template_url'] = template_url
        if environment is not None:
            if use_all_urls is True:
                environment=json.loads(urlopen(environment).read())
            data['environment'] = environment    
        if parameters is not None:
            if use_all_urls is True:
                parameters=json.loads(urlopen(parameters).read())
            data['parameters'] = parameters
        if timeout_mins is not None:
            data['timeout_mins'] = timeout_mins
        if files is not None:
            if use_all_urls is True:
                files=json.loads(urlopen(files).read())
            data['files'] = files
        if tags is not None:
            data['tags'] = tags            
        if disable_rollback is False:
            data['disable_rollback'] = 'FALSE'

        #print data
        path = '/stacks/preview'
        self.logger.debug('-------------data: %s'%json.dumps(data))
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Preview openstack heat stack: %s' % truncate(res))
        return res[0]

    def stacks_update(self, stack_name, ext_id, template_url=None, template=None, 
               environment=None, files=None, parameters=None, tags=None,
               timeout_mins=None, disable_rollback=True, use_all_urls=False):
        """ Update a stack.
        
        :param Same params present in create module +
        :param ext_id: The UUID of the stack.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: stack id and stack links
        
        Example
        
        .. code-block:: python
                 
            {
                "stack": {
                    "id": "3095aefc-09fb-4bc7-b1f0-f21a304e864c",
                    "links": [
                        {
                            "href": "http://192.168.123.200:8004/v1/eb1c63a\
                            4f77141548385f113a28f0f52/stacks/teststack/3095\
                            aefc-09fb-4bc7-b1f0-f21a304e864c",
                            "rel": "self"
                        }
                    ]
                }
            }        
        """
        
        data={}
        
        if stack_name is not None and ext_id is not None:
            if template is not None:
                data['template'] = template
            if template_url is not None:
                data['template_url'] = template_url
            if environment is not None:
                if use_all_urls is True:
                    environment=json.loads(urlopen(environment).read())
                data['environment'] = environment    
            if parameters is not None:
                if use_all_urls is True:
                    parameters=json.loads(urlopen(parameters).read())
                data['parameters'] = parameters
            if timeout_mins is not None:
                data['timeout_mins'] = timeout_mins
            if files is not None:
                if use_all_urls is True:
                    files=json.loads(urlopen(files).read())
                data['files'] = files
            if tags is not None:
                data['tags'] = tags            
            if disable_rollback is False:
                data['disable_rollback'] = 'FALSE'

            path = '/stacks/%s/%s'%(stack_name,ext_id)
            
            self.logger.debug('-------------data: %s'%json.dumps(data))
            res = self.client.call(path, 'PUT', data=json.dumps(data), 
                                   token=self.manager.identity.token)
            self.logger.debug('Update openstack heat stack: %s' % truncate(res))
        else:
            raise OpenstackError("You must specify both stack name and stack UUID", 404)     
                
        return res[0]

    def stacks_update_preview(self, stack_name, ext_id, template_url=None, template=None, 
               environment=None, files=None, parameters=None, tags=None,
               timeout_mins=None, use_all_urls=False):
        """Preview a stack update.
        
        :param Same params present in create module -disable_rollback +ext_id
        :param ext_id: The UUID of the stack.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: chamgements dictionary
        """
        
        data={}
        
        if stack_name is not None and ext_id is not None:
            if template is not None:
                data['template'] = template
            if template_url is not None:
                data['template_url'] = template_url
            if environment is not None:
                if use_all_urls is True:
                    environment=json.loads(urlopen(environment).read())
                data['environment'] = environment    
            if parameters is not None:
                if use_all_urls is True:
                    parameters=json.loads(urlopen(parameters).read())
                data['parameters'] = parameters
            if timeout_mins is not None:
                data['timeout_mins'] = timeout_mins
            if files is not None:
                if use_all_urls is True:
                    files=json.loads(urlopen(files).read())
                data['files'] = files
            if tags is not None:
                data['tags'] = tags            

            path = '/stacks/%s/%s/preview'%(stack_name,ext_id)
            
            self.logger.debug('-------------data: %s'%json.dumps(data))
            res = self.client.call(path, 'PUT', data=json.dumps(data), 
                                   token=self.manager.identity.token)
            self.logger.debug('Preview update openstack heat stack: %s' % truncate(res))
        else:
            raise OpenstackError("You must specify both stack name and stack UUID", 404)     
                
        return res[0]

    def stacks_find(self, stack_name=None):
        """GET the Stack List
         
        :param stack_name: The name of a stack. 
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks"
        if stack_name is not None:
#             try:
            res=self.list(name=stack_name)
            res['stacks'][0]['links'][0]['href']
#             except:
#                 raise OpenstackError("No stack found", 404)   

             
        else:
            raise OpenstackError("No stack name specified", 404)   
         
        self.logger.debug('Find openstack heat stack: %s' % \
                          truncate(res['stacks'][0]['links'][0]['href']))
        return res['stacks'][0]['links'][0]['href']

    def stacks_details(self, stack_name, ext_id):
        """GET the Stack Details
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s"%(stack_name,ext_id)
        if stack_name is not None and ext_id is not None:
            res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        else:
            raise OpenstackError("You must specify both stack name and stack UUID", 404)   
         
        self.logger.debug('Openstack heat stack Details: %s' % \
                          truncate(res))
        return res[0]
    
    def stacks_delete(self, stack_name, ext_id):
        """DELETE a Stack
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s"%(stack_name,ext_id)
        if stack_name is not None and ext_id is not None:
            res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        else:
            raise OpenstackError("You must specify both stack name and stack UUID", 404)   
         
        self.logger.debug('Openstack heat stack Delete: %s' % \
                          truncate(res))
        return res[0]    

    def snapshots_list(self, stack_name, ext_id):
        """GET the snapshots list
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s/snapshots"%(stack_name,ext_id)
        if stack_name is not None and ext_id is not None:
            res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        else:
            raise OpenstackError("You must specify both stack name and stack UUID", 404)   
         
        self.logger.debug('Openstack heat snapshots list: %s' % \
                          truncate(res))
        return res[0]

    def snapshots_create(self, stack_name, ext_id, name):
        """Create a snapshot
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :param name: The name for the snapshot.        
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        
        :note: From Mitaka docs, force flag problem will be removed
            Consistency Groups
            ==================
            CG APIs are disabled by default by policy. It was brought up whether
            this should now change. Since not every backend support CGs it was
            decided we will not change this.
            There's no force flag for CG snapshots unlike individial volume APIs.
            This led to a broader discussion on the need for the force flag in
            the first place. General agreement was it should probably just be
            removed.
            Quotas with CG snapshots - is a new quota needed? Determined existing
            volume quotas are all that's needed and nothing special for CGs.
        
        """
        
        path="/stacks/%s/%s/snapshots"%(stack_name,ext_id)
        data={}
        if stack_name is not None and ext_id is not None:
            if name is not None:
                data['name'] = name
            self.logger.debug('-------------data: %s'%json.dumps(data))
            res = self.client.call(path, 'POST', data=json.dumps(data), 
                                   token=self.manager.identity.token)
            self.logger.debug('Update openstack heat stack: %s' % truncate(res))
        else:
            raise OpenstackError("You must specify both stack name and stack UUID", 404)     
         
        self.logger.debug('Openstack heat snapshots list: %s' % \
                          truncate(res))
        return res[0]

    def snapshots_show(self, stack_name, ext_id, snapshot_id):
        """Show snapshot Details
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :param snapshot_id: The UUID of the snapshot.        
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s/snapshots/%s"%(stack_name,ext_id,snapshot_id)
        if stack_name is not None and ext_id is not None and snapshot_id is not None:
            res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        else:
            raise OpenstackError("You must specify stack name, stack UUID and snapshot_id", 404)   
         
        self.logger.debug('Openstack heat snapshots show: %s' % \
                          truncate(res))
        return res[0]
    
    def snapshots_restore(self, stack_name, ext_id, snapshot_id):
        """restore a snapshot
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :param snapshot_id: The UUID of the snapshot.        
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s/snapshots/%s/restore"%(stack_name,ext_id,snapshot_id)
        if stack_name is not None and ext_id is not None and snapshot_id is not None:
            res = self.client.call(path, 'POST', data='', token=self.manager.identity.token)
        else:
            raise OpenstackError("You must specify stack name, stack UUID and snapshot_id", 404)   
         
        self.logger.debug('Openstack heat snapshots restore: %s' % \
                          truncate(res))
        return res[0]

    def snapshots_delete(self, stack_name, ext_id, snapshot_id):
        """DELETE a snapshot
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :param snapshot_id: The UUID of the snapshot.        
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s/snapshots/%s"%(stack_name,ext_id,snapshot_id)
        if stack_name is not None and ext_id is not None and snapshot_id is not None:
            res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        else:
            raise OpenstackError("You must specify stack name, stack UUID and snapshot_id", 404)   
         
        self.logger.debug('Openstack heat snapshots delete: %s' % \
                          truncate(res))
        return res[0]

    def outputs_find(self, stack_name, ext_id, output_key=None):
        """GET the outputs of a stack (if exist)
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :param output_key: The name of a particular key to be shown      
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s"%(stack_name,ext_id)
        if stack_name is not None and ext_id is not None:
            res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
            if 'outputs' in res[0]['stack']:
                if output_key is None:
                    res = {'outputs':res[0]['stack']['outputs']}
                else:
                    for item in res[0]['stack']['outputs']:
                        if output_key == str(item['output_key']):
                            res = {'output':item}
                            self.logger.debug('Openstack heat stack list outputs: %s' % \
                                              truncate(res)) 
                            return res                           
                        else:
                            res = {'output': []} 
            else:
                if output_key is None:
                    res = {'outputs': []}
                else:
                    res = {'output': []}
        else:
            raise OpenstackError("You must specify stack name, stack UUID and snapshot_id", 404)   
         
        self.logger.debug('Openstack heat stack list outputs: %s' % \
                          truncate(res))
        return res
    
    def resources_find(self, stack_name, ext_id, resource_name=None):
        """GET the resources of a stack (if exist)
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :param resource_name: The name of a particular key to be shown      
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s/resources?nested_depth=1&with_detail=True"%(stack_name,ext_id)
        if stack_name is not None and ext_id is not None:

            #print res[0]
            if resource_name is None:
                res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
                res = {'resources':res[0]['resources']}
            else:
                res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
                for item in res[0]['resources']:
                    if item['resource_name'] == resource_name:
                        self.logger.debug('Openstack heat stack find resource: %s' % \
                          truncate(item))
                        return {'resource':item}
                res = []
                    
        else:
            raise OpenstackError("You must specify stack name, stack UUID and snapshot_id", 404)   
          
        self.logger.debug('Openstack heat stack list resources: %s' % \
                          truncate(res))
        return res

    def resources_find_metadata(self, stack_name, ext_id, resource_name):
        """GET the resources metadata for a stack resource
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :param resource_name: The name of a particular key to be shown      
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s/resources/%s/metadata"%(stack_name,ext_id,resource_name)
        if stack_name is not None and ext_id is not None:
            res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        else:
            raise OpenstackError("You must specify stack name, stack UUID and snapshot_id", 404)   
          
        self.logger.debug(u'Openstack heat stack list resources: %s' % \
                         truncate(res))
        return res[0]
    
    def resources_send_signal(self, stack_name, ext_id, resource_name, 
                              signal_data=None):
        """Send signal to a resource
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :param resource_name: The name of a particular key to be shown
        :param signal_data: Colud be everytingh. Some resources cannot receive 
            signals. If you send them a signal, they return a 400 error code.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s/resources/%s/signal"%(stack_name,ext_id,resource_name)
        if stack_name is not None and ext_id is not None:
            res = self.client.call(path, 'POST', data=json.dumps(signal_data), 
                                   token=self.manager.identity.token)
        else:
            raise OpenstackError("You must specify stack name, stack UUID and snapshot_id", 404)   
          
        self.logger.debug('Openstack heat send resource signal: %s' % \
                          truncate(res))
        return res[0]    


    def resource_types_list(self):
        """Lists all supported template resource types. 
         
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: json
        
        Example
        
        .. code-block:: python        
        
            {
               "resource_types":[
                  "AWS::AutoScaling::AutoScalingGroup",
                  "AWS::AutoScaling::LaunchConfiguration",
                  "AWS::AutoScaling::ScalingPolicy",
                  "AWS::CloudFormation::Stack",
                  "AWS::CloudFormation::WaitCondition",
                  "AWS::CloudFormation::WaitConditionHandle",
                  "AWS::CloudWatch::Alarm",
                  "AWS::EC2::EIP",
                  "AWS::EC2::EIPAssociation",
                  "AWS::EC2::Instance",
                  "AWS::EC2::InternetGateway",
                  "AWS::EC2::NetworkInterface",
                  "AWS::EC2::RouteTable",
                  "AWS::EC2::SecurityGroup",
                  "AWS::EC2::Subnet",
                  "AWS::EC2::SubnetRouteTableAssociation",
                  "AWS::EC2::VPC",
                  "AWS::EC2::VPCGatewayAttachment",
                  "AWS::EC2::Volume",
                  "AWS::EC2::VolumeAttachment",
                  "AWS::ElasticLoadBalancing::LoadBalancer",
                  "AWS::IAM::AccessKey",
                  "AWS::IAM::User",
                  "AWS::RDS::DBInstance",
                  "AWS::S3::Bucket",
                  "OS::Ceilometer::Alarm",
                  "OS::Ceilometer::CombinationAlarm",
                  "OS::Ceilometer::GnocchiAggregationByMetricsAlarm",
                  "OS::Ceilometer::GnocchiAggregationByResourcesAlarm",
                  "OS::Ceilometer::GnocchiResourcesAlarm",
                  "OS::Cinder::EncryptedVolumeType",
                  "OS::Cinder::Volume",
                  "OS::Cinder::VolumeAttachment",
                  "OS::Cinder::VolumeType",
                  "OS::Glance::Image",
                  "OS::Heat::AccessPolicy",
                  "OS::Heat::AutoScalingGroup",
                  "OS::Heat::CloudConfig",
                  "OS::Heat::HARestarter",
                  "OS::Heat::InstanceGroup",
                  "OS::Heat::MultipartMime",
                  "OS::Heat::None",
                  "OS::Heat::RandomString",
                  "OS::Heat::ResourceGroup",
                  "OS::Heat::ScalingPolicy",
                  "OS::Heat::SoftwareComponent",
                  "OS::Heat::SoftwareConfig",
                  "OS::Heat::SoftwareDeployment",
                  "OS::Heat::SoftwareDeploymentGroup",
                  "OS::Heat::SoftwareDeployments",
                  "OS::Heat::Stack",
                  "OS::Heat::StructuredConfig",
                  "OS::Heat::StructuredDeployment",
                  "OS::Heat::StructuredDeploymentGroup",
                  "OS::Heat::StructuredDeployments",
                  "OS::Heat::SwiftSignal",
                  "OS::Heat::SwiftSignalHandle",
                  "OS::Heat::TestResource",
                  "OS::Heat::UpdateWaitConditionHandle",
                  "OS::Heat::WaitCondition",
                  "OS::Heat::WaitConditionHandle",
                  "OS::Keystone::Endpoint",
                  "OS::Keystone::Group",
                  "OS::Keystone::GroupRoleAssignment",
                  "OS::Keystone::Project",
                  "OS::Keystone::Role",
                  "OS::Keystone::Service",
                  "OS::Keystone::User",
                  "OS::Keystone::UserRoleAssignment",
                  "OS::Neutron::ExtraRoute",
                  "OS::Neutron::Firewall",
                  "OS::Neutron::FirewallPolicy",
                  "OS::Neutron::FirewallRule",
                  "OS::Neutron::FloatingIP",
                  "OS::Neutron::FloatingIPAssociation",
                  "OS::Neutron::HealthMonitor",
                  "OS::Neutron::IKEPolicy",
                  "OS::Neutron::IPsecPolicy",
                  "OS::Neutron::IPsecSiteConnection",
                  "OS::Neutron::LoadBalancer",
                  "OS::Neutron::MeteringLabel",
                  "OS::Neutron::MeteringRule",
                  "OS::Neutron::Net",
                  "OS::Neutron::NetworkGateway",
                  "OS::Neutron::Pool",
                  "OS::Neutron::PoolMember",
                  "OS::Neutron::Port",
                  "OS::Neutron::ProviderNet",
                  "OS::Neutron::Router",
                  "OS::Neutron::RouterInterface",
                  "OS::Neutron::SecurityGroup",
                  "OS::Neutron::Subnet",
                  "OS::Neutron::VPNService",
                  "OS::Nova::Flavor",
                  "OS::Nova::FloatingIP",
                  "OS::Nova::FloatingIPAssociation",
                  "OS::Nova::KeyPair",
                  "OS::Nova::Server",
                  "OS::Nova::ServerGroup",
                  "OS::Swift::Container"
               ]
            }        
        """
        
        path="/resource_types"
        res = self.client.call(path, 'GET', data='', 
                                   token=self.manager.identity.token)
        self.logger.debug('Openstack heat resource tipe list: %s' % \
                          truncate(res))
        return {'resource_types':sorted(res[0]['resource_types'])}

    def resource_types_show(self,resource_type):
        """Shows the resource type charateristics
         
        :param resource_type: The name of a resource type.        
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: json
        
        Example
        
        .. code-block:: python          
        
            {
               "support_status":{ },
               "attributes":{
                  "console_urls":{ },
                  "name":{ },
                  "first_address":{ },
                  "show":{ },
                  "instance_name":{ },
                  "accessIPv4":{ },
                  "accessIPv6":{ },
                  "networks":{ },
                  "addresses":{ }
               },
               "properties":{
                  "admin_pass":{ },
                  "availability_zone":{ },
                  "image":{ },
                  "user_data":{ },
                  "diskConfig":{ },
                  "flavor_update_policy":{ },
                  "flavor":{ },
                  "reservation_id":{ },
                  "networks":{ },
                  "security_groups":{ },
                  "scheduler_hints":{ },
                  "metadata":{ },
                  "personality":{ },
                  "user_data_format":{ },
                  "admin_user":{ },
                  "block_device_mapping":{ },
                  "key_name":{ },
                  "software_config_transport":{ },
                  "name":{ },
                  "block_device_mapping_v2":{ },
                  "image_update_policy":{ },
                  "config_drive":{ }
               },
               "resource_type":"OS::Nova::Server"
            }
        """
        
        path="/resource_types/%s" %resource_type
        res = self.client.call(path, 'GET', data='', 
                                   token=self.manager.identity.token)
        self.logger.debug('Openstack heat resource types show: %s' % \
                          truncate(res))
        return res[0] 

    def resource_types_template(self,resource_type,template_type ='hot'):
        """Shows the resource type charateristics for a particular template.
         
        :param template_type: The resource template type. Default type is cfn. 
            The hot template type is supported. 
        :param resource_type: The name of a resource type.        
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: json
        
        Example
        
        .. code-block:: python
                
            {
                "outputs":{
                    "console_urls":{ },
                    "name":{ },
                    "first_address":{ },
                    "show":{ },
                    "instance_name":{ },
                    "accessIPv4":{ },
                    "accessIPv6":{ },
                    "networks":{ },
                    "addresses":{ }
                },
                "heat_template_version":"2015-04-30",
                "description":"Initial template of Server",
                "parameters":{
                    "admin_pass":{ },
                    "availability_zone":{ },
                    "image":{ },
                    "user_data":{ },
                    "diskConfig":{ },
                    "flavor_update_policy":{ },
                    "flavor":{ },
                    "reservation_id":{ },
                    "networks":{ },
                    "security_groups":{ },
                    "scheduler_hints":{ },
                    "metadata":{ },
                    "personality":{ },
                    "user_data_format":{ },
                    "admin_user":{ },
                    "block_device_mapping":{ },
                    "key_name":{ },
                    "software_config_transport":{ },
                    "name":{ },
                    "block_device_mapping_v2":{ },
                    "image_update_policy":{ },
                    "config_drive":{ }
                },
                "resources":{
                    "Server":{
                       "type":"OS::Nova::Server",
                       "properties":{ }
                    }
                }
            }
        """
        
        path="/resource_types/%s/template?template_type=%s" % \
                        (resource_type,template_type)
        res = self.client.call(path, 'GET', data='', 
                                   token=self.manager.identity.token)
        self.logger.debug('Openstack heat resources types template: %s' % \
                          truncate(res))
        return res[0]           

    def events_list(self, stack_name, ext_id, resource_action=None, resource_status=None):
        """List the Stack Events
         
        :param stack_name: The name of a stack.
        :param ext_id: The UUID of the stack.
        :param resource_action: [optional] Filters the event list by a resource 
            action. You can use this filter multiple times to filter by multiple 
            resource actions. Valid resource actions are ADOPT, CHECK, CREATE, 
            DELETE, INIT, RESTORE, RESUME, ROLLBACK, SNAPSHOT, SUSPEND, and UPDATE.
        :param resource_status: [optional] Filters the event list by a resource 
            status. You can use this filter multiple times to filter by multiple 
            resource statuses. Valid resource statuses are COMPLETE, FAILED, 
            and IN_PROGRESS. 
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: Heat Stack List
        """
        
        path="/stacks/%s/%s/events"%(stack_name,ext_id)
        if stack_name is not None and ext_id is not None:

            data={}
            
            if stack_name is not None and ext_id is not None:
                if resource_action is not None:
                    data['resource_action'] = resource_action
                if resource_status is not None:
                    data['resource_status'] = resource_status


                path = '%s?%s' % (path, urlencode(data))
                res = self.client.call(path, 'GET', data='', 
                                       token=self.manager.identity.token)
        else:
            raise OpenstackError("You must specify both stack name and stack UUID", 404)   
         
        self.logger.debug('Openstack heat stack Events: %s' % \
                          truncate(res))
        return res[0]
    
    def template_versions(self):
        """GET the template versions

        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        path="/template_versions"
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Openstack template versions: %s' % \
                          truncate(res))
        return res[0]

    def template_validate(self, template_url=None, template=None, 
               environment=None, use_all_urls=False):
        """Validate a Template.
        
        :param template_url: [optional] A URI to the location containing the
            stack template on which to perform the operation. See the
            description of the template parameter for information about the
            expected template content located at the URI. This parameter is
            only required when you omit the template parameter. If you
            specify both parameters, this parameter is ignored. 
        :param template: The stack template on which to perform the operation.
            This parameter is always provided as a string in the JSON request
            body. The content of the string is a JSON- or YAML-formatted
            Orchestration template. For example:
            
            .. code-block:: python            
            
                "template": {
                    "heat_template_version": "2013-05-23",
                    ...,
                } 
            
            This parameter is required only when you omit the template_url
            parameter. If you specify both parameters, this value overrides
            the template_url parameter value. 
        :param environment: [optional] A JSON environment for the stack.         
        :param use_all_urls: [optional] set yes if need to use an environment URL 
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return:      
        """
        
        data={}
    
        if template is not None:
            data['template'] = template
        if template_url is not None:
            data['template_url'] = template_url
        if environment is not None:
            if use_all_urls is True:
                environment=json.loads(urlopen(environment).read())
            data['environment'] = environment    

        path = '/validate'
        
        self.logger.debug('-------------data: %s'%json.dumps(data))
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Validate openstack heat template: %s' % truncate(res))
                
        return res[0]

    def build_info(self):
        """Shows build information for an Orchestration deployment. 

        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        path='/build_info'
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Openstack build info: %s' % \
                          truncate(res))
        return res[0]

    def software_configs_list(self):
        """Lists all available software configs. 

        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        path='/software_configs'
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Openstack List configs: %s' % \
                          truncate(res))
        return res[0]['software_configs']
    
    def software_configs_details(self, config_id):
        """Shows software config details for a config id. 
        
        :param config_id: the ID of the config
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        path='/software_configs/%s'%config_id
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Openstack shows config details: %s' % \
                          truncate(res))
        return res[0]['software_config']    

    def software_configs_delete(self, config_id):
        """Shows software config details for a config id. 
        
        :param config_id: the ID of the config
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        path='/software_configs/%s'%config_id
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Openstack delete config: %s' % \
                          truncate(res))
        return res[0]    

    def software_configs_create(self,config=None,group=None,name=None,
                    inputs=None,outputs=None,options=None,use_all_urls=True):
        """Creates a software configuration. 

        :param config: [optional] Configuration script or manifest that 
            defines which configuration is performed. Must be a URI file if 
            use_all_urls is set to True.
        :param group: [optional] Namespace that groups this software
            configuration by when it is delivered to a server. This setting might
            simply define which configuration tool performs the configuration.
            Values admitted: ansible, cfn-init, chef, docker, docker-compose, 
            kubelet, puppet, salt, script.
        :param name: [optional] The name of the configuration to create.
        :param inputs: [optional] Schema that represents the inputs that 
            this software configuration expects. Must be a URI file if 
            use_all_urls is set to True.
        :param outputs: [optional] Schema that represents the outputs that 
            this software configuration produces. Must be a URI file if 
            use_all_urls is set to True.
        :param options: [optional] Map that contains options that are specific
            to the configuration management tool that this resource uses.
        :param use_all_urls: [optional] Default False. Must be True if you 
            need to pass inputs and outputs as files in a URL
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        data = {}
        
        if config is not None:
            if use_all_urls is True:
                config=json.loads(urlopen(config).read())            
            data['config'] = config
        if group is not None:
            data['group'] = group
        if name is not None:
            data['name'] = name            
        if inputs is not None:
            if use_all_urls is True:
                inputs=json.loads(urlopen(inputs).read())
            data['inputs'] = inputs    
        if outputs is not None:
            if use_all_urls is True:
                outputs=json.loads(urlopen(outputs).read())
            data['outputs'] = outputs
        if options is not None:
            data['options'] = options  
        
        path='/software_configs'
        res = self.client.call(path, 'POST',  data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Openstack create software configs: %s' % \
                          truncate(res))
        return res[0]

    def software_deployments_list(self):
        """Lists all available software deployments. 

        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        out={}
        path='/software_deployments'
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Openstack List deployments: %s' % \
                          truncate(res))
        for item in res[0]['software_deployments']:
            try:
                del item['input_values']
                del item['output_values']
            except KeyError:
                pass
            
        return res[0]['software_deployments']

    def software_deployments_details(self,deployment_id):
        """Shows software deployment detail. 

        :param deployment_id: the ID of the deployment
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        path='/software_deployments/%s' %deployment_id
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get heat show deployment details: %s' %res[0])
        return res[0]['software_deployment']


    def software_deployments_show_metadata(self,server_id):
        """Shows software deployment detail. 

        :param server_id: the ID of metadata server
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
      
        path='/software_deployments/metadata/%s' %server_id
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get heat server metadata: %s' % \
                          truncate(res))
        return res[0]

    def software_deployments_create(self,config_id,server_id,action,
                    stack_user_project_id=None, status=None,status_reason=None):
        """Creates a software deployment. 

        :param config_id: The UUID of the software configuration resource that runs
            when applying to the server.
        :param server_id: The UUID of the compute server to which the configuration applies.
        :param action: The current stack action that triggers this deployment resource.
        :param stack_user_project_id: [optional] Authentication project ID, which can
            also perform operations on this deployment.
        :param status: [optional] Current status of the deployment. A valid value is
            COMPLETE, IN_PROGRESS, or FAILED. the resource remains in an 
            IN_PROGRESS state until the server signals to heat what (if any) 
            output values were generated by the config script.
        :param status_reason: [optional] Error description for the last status change,
            which is FAILED status.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        data = {}
        
        if config_id is not None:
            data['config_id'] = config_id
        if server_id is not None:
            data['server_id'] = server_id
        if action is not None:
            data['action'] = action            
        if stack_user_project_id is not None:
            data['stack_user_project_id'] = stack_user_project_id    
        if status is not None:
            data['status'] = status
        if status_reason is not None:
            data['status_reason'] = status_reason  
        
        path='/software_deployments'
        res = self.client.call(path, 'POST',  data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Openstack create software software_deployments: %s' % \
                          truncate(res))
        return res[0]

    def software_deployments_update(self, config_id, deployment_id, action, 
                    status=None, status_reason=None, output_values=None,
                    use_all_urls=False):
        """Updates a software deployment. 

        :param config_id: The UUID of the software configuration resource that runs
            when applying to the server.
        :param deployment_id: The UUID of the deployment.
        :param action: The current stack action that triggers this deployment resource.
        :param status: [optional] Current status of the deployment. A valid value is
            COMPLETE, IN_PROGRESS, or FAILED. the resource remains in an 
            IN_PROGRESS state until the server signals to heat what (if any) 
            output values were generated by the config script.
        :param status_reason: [optional] Error description for the last status change,
            which is FAILED status.
        :param output_values: [optional] Map of output values for the deployment, 
            as signaled from the server. 
        :param use_all_urls: [optional] Default False. Must be True if you 
            need to pass inputs and outputs as files in a URL 
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        data = {}
        
        if config_id is not None:
            data['config_id'] = config_id
        if action is not None:
            data['action'] = action            
        if status is not None:
            data['status'] = status
        if status_reason is not None:
            data['status_reason'] = status_reason
        if output_values is not None:
            if use_all_urls is True:
                output_values=json.loads(urlopen(output_values).read())
            data['output_values'] = output_values           
        
        path='/software_deployments/%s'%deployment_id
        res = self.client.call(path, 'PUT',  data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Openstack update software deployments: %s' % \
                          truncate(res))
        return res[0]
    
    def software_deployments_delete(self, deployment_id):
        """Shows software config details for a config id. 
        
        :param deployment_id: the ID of the config
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        path='/software_deployments/%s'%deployment_id
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Openstack delete deployment: %s' % \
                          truncate(res))
        return res[0]    
    

    def services_status(self):
        """Show orchestration engine status

        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dictionary
        """
        
        path="/services"
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Openstack template versions: %s' % \
                          truncate(res))
        return res[0]
