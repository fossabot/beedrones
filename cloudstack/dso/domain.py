'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .account import Account

class Domain(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        self._obj_type = 'domain'

    def info(self, cache=True):
        '''Describe domain'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listDomains',
                  'domainid':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listdomainsresponse']['domain'][0]
            self._data = res
            return self._data
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)

    def delete(self, job_id):
        """Delete the domain.
        Async command.
        """        
        params = {'command':'deleteDomain',
                  'id':self._id,
                  'cleanup':True}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['deletedomainresponse']['jobid']
            job_res = self._api_client.query_async_job(job_id, clsk_job_id, delta=1)
            
            self.logger.debug('Removed domain: %s, %s' % (self.info()['name'], 
                                                          self.info()['id']))
            return job_res
        except KeyError:
            raise ClskObjectError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)  

    def tree(self):
        '''Return zone tree.'''
        domain = {'name':self._name, 
                'id':self._id, 
                'type':self._obj_type, 
                'childs':[]}        
        for account in self.list_accounts():
            domain['childs'].append(account.tree())
        return domain

    def list_accounts(self):
        ''' list accounts'''
        if not self.id:
            self.info()
            
        params = {'command':'listAccounts',
                  'domainid':self.id,
                  'response':'json',}
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listaccountsresponse']
            if len(res) > 0:
                data = res['account']
            else:
                return []
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        accounts = []
        for item in data:
            # create Account instance
            account = Account(self._api_client, item)
            accounts.append(account)
        
        return accounts        
        
    def create_account(self, name, type, 
                       firstname, lastname, username, password,
                       email, timezone='CET'):
        '''Create account
        
        :param type: USER, ROOT, ADMIN
        :param domain_id: value like 2602ce61-59b5-4068-bf9b-a85101fae4be'''
        if not self.id:
            self.info()        
        
        if type == 'USER':
            type = 0
        elif type == 'ROOT':
            type = 1
        elif type == 'ADMIN':
            type = 2
        
        params = {'command':'createAccount',
                  'account':name,
                  'domainid':self.id,
                  'accounttype':type,
                  'firstname':firstname,
                  'lastname':lastname,
                  'username':username,
                  'password':password,
                  'timezone':timezone,
                  'email':email,
                 }

        try:
            response = self._api_client.send_api_request(params)
            data = json.loads(response)['createaccountresponse']['account']
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)

        # create Account instance
        account = Account(self._api_client, data)
            
        return account