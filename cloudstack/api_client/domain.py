"""
Created on May 10, 2013

@author: darkbk
"""
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from .account import Account

class Domain(ClskObject):
    """Domain api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'domain'

    def __str__(self):
        return "<%s id='%s', name='%s' path='%s' parent='%s'>" % (
                    self._obj_type, self.id, self.name, self.path, 
                    self.parentdomainid)

    def __repr__(self):
        return "<%s id='%s', name='%s' path='%s' parent='%s'>" % (
                    self._obj_type, self.id, self.name, self.path, 
                    self.parentdomainid)

    @watch
    def delete(self):
        """Delete the domain.
        
        *Async command*

        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deleteDomain',
                  'id':self.id,
                  'cleanup':True}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deletedomainresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'deleteDomain', res))
            return clsk_job_id
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)  

    @watch
    def tree(self):
        """Return domain tree.

        :return: Dictionary with all the info
        :rtype: dict       
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        domain = {'name':self.name, 
                  'id':self.id, 
                  'type':self._obj_type, 
                  'childs':[]}        
        for account in self.list_accounts():
            domain['childs'].append(account.tree())
        return domain

    @watch
    def list_accounts(self):
        """List accounts.
        
        :return: List of :class:`Account`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError` 
        """
        params = {'command':'listAccounts',
                  'domainid':self.id,
                  'response':'json'}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listaccountsresponse']
            if len(res) > 0:
                data = res['account']
            else:
                data = []
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
        
        accounts = []
        for item in data:
            # create Account instance
            account = Account(self._orchestrator, item)
            accounts.append(account)
            
        self.logger.debug("List domain %s accounts: %s" % (self.name, 
                                                           accounts))
        
        return accounts        
        
    @watch
    def create_account(self, name, atype, firstname, lastname, username, 
                             password, email, timezone='CET'):
        """Create account
        
        :param str name: account name
        :param str type: USER, ROOT, ADMIN
        :param str firstname: account user firstname
        :param str lastname: account user lastname
        :param str username: account user username
        :param str password: account user password
        :param str email: account user email
        :param str timezone: account user timezone [default=CET]
        
        :return: :class:`Account` instance
        :rtype: :class:`Account`
        :raises ClskError: raise :class:`.base.ClskError`         
        """
        if atype == 'USER':
            atype = 0
        elif atype == 'ROOT':
            atype = 1
        elif atype == 'ADMIN':
            atype = 2
        
        params = {'command':'createAccount',
                  'account':name,
                  'domainid':self.id,
                  'accounttype':atype,
                  'firstname':firstname,
                  'lastname':lastname,
                  'username':username,
                  'password':password,
                  'timezone':timezone,
                  'email':email}

        try:
            response = self.send_request(params)
            data = json.loads(response)['createaccountresponse']['account']
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)

        # create Account instance
        account = Account(self._orchestrator, data)
        self.logger.debug("Create domain %s account: %s" % (self.name, 
                                                            account))
            
        return account

    @watch
    def delete_account(self, account_id):
        """Delete account

        *Async command*

        :param str account_id: id of the account to delete
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`    
        """
        params = {'command':'deleteAccount',
                  'id':account_id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deleteaccountresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'deleteAccount', res))
            return clsk_job_id
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)