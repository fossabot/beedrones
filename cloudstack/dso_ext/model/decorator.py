'''
Created on Jan 31, 2014

@author: darkbk
'''
import time
from functools import wraps
import logging
from sqlalchemy.exc import IntegrityError, DBAPIError
from gibbonutil.simple import id_gen

logger = logging.getLogger('gibbon.cloud')

class TransactionError(Exception): pass
class QueryError(Exception): pass

def transaction(manager):
    """Use this decorator to transform a function that contains delete, insert
    and update statement in a transaction.
    
    :param manager: Object with method get_session(), release_session()
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            start = time.time()
            stmp_id = id_gen()            
            try:
                session = manager.get_session()
            except Exception as ex:
                raise TransactionError(ex)
                
            try:
                logger.debug('Transaction id:%s  - start' % stmp_id)
                res = fn(session, *args, **kwargs)
                session.commit()
                elapsed = round(time.time() - start, 4)
                logger.debug('Transaction id:%s  - stop [%s]' % (stmp_id, elapsed))
                return res            
            except IntegrityError as ex:
                elapsed = round(time.time() - start, 4)
                logger.error('Transaction id:%s  - error: %s [%s]' % (stmp_id, ex, elapsed))
                session.rollback()
                raise TransactionError(ex)
            except DBAPIError as ex:
                elapsed = round(time.time() - start, 4)
                logger.error('Transaction id:%s  - error: %s [%s]' % (stmp_id, ex, elapsed))
                session.rollback()
                raise TransactionError(ex)            
            finally:
                manager.release_session(session)
                
        return decorated_view
    return wrapper

def query(manager):
    """Use this decorator to transform a function that contains delete, insert
    and update statement in a transaction.
    
    :param manager: Object with method get_session(), release_session()
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            start = time.time()
            stmp_id = id_gen()
            
            try:
                session = manager.get_session()
            except Exception as ex:
                raise QueryError(ex)
                
            try:
                logger.debug('Query id:%s - start' % stmp_id)
                res = fn(session, *args, **kwargs)
                elapsed = round(time.time() - start, 4)
                logger.debug('Query id:%s  - stop [%s]' % (stmp_id, elapsed))
                return res
            except DBAPIError as ex:
                elapsed = round(time.time() - start, 4)
                logger.error('Query id:%s  - error [%s] : %s' % (stmp_id, ex, elapsed))
                raise QueryError(ex)            
            finally:
                manager.release_session(session)
                
        return decorated_view
    return wrapper