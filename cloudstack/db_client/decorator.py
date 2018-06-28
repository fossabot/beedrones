'''
Created on Jan 31, 2014

@author: darkbk
'''
import time
from functools import wraps
import logging
from sqlalchemy.exc import IntegrityError, DBAPIError
from beecell.simple import id_gen

logger = logging.getLogger('gibbon.cloud.db')

class TransactionError(Exception): pass
class QueryError(Exception): pass

def transaction(session):
    """Use this decorator to transform a function that contains delete, insert
    and update statement in a transaction.
    
    :param session: Database session
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            start = time.time()
            stmp_id = id_gen()
            try:
                logger.debug('Transaction %s - START' % stmp_id)
                res = fn(session, *args, **kwargs)
                session.commit()
                elapsed = round(time.time() - start, 4)
                logger.debug('Transaction %s - STOP - %s' % (stmp_id, elapsed))
                return res            
            except IntegrityError as ex:
                elapsed = round(time.time() - start, 4)
                logger.error('Transaction %s - ERROR: %s - %s' % (stmp_id, ex, elapsed))
                session.rollback()
                raise TransactionError(ex)
            except DBAPIError as ex:
                elapsed = round(time.time() - start, 4)
                logger.error('Transaction %s - ERROR: %s - %s' % (stmp_id, ex, elapsed))
                session.rollback()
                raise TransactionError(ex)
                
        return decorated_view
    return wrapper

def query(session):
    """Use this decorator to transform a function that contains delete, insert
    and update statement in a transaction.
    
    :param session: Database session
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            start = time.time()
            stmp_id = id_gen()
            try:
                logger.debug('Query %s - START' % stmp_id)
                res = fn(session, *args, **kwargs)
                elapsed = round(time.time() - start, 4)
                logger.debug('Query %s - STOP - %s' % (stmp_id, elapsed))
                return res
            except DBAPIError as ex:
                elapsed = round(time.time() - start, 4)
                logger.error('Query %s - ERROR - %s : %s' % (stmp_id, ex, elapsed))
                raise QueryError(ex)
                
        return decorated_view
    return wrapper