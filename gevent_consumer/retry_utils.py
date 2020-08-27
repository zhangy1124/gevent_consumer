# coding=utf-8
import time
import socket
import logging

from functools import wraps

try:
    from thriftpy2.thrift import TException
except ImportError:
    from thriftpy.thrift import TException

from django.db import connection
from django.db.utils import OperationalError


logger = logging.getLogger(__name__)


"""
hbase err statistic
1. [time out]
maybe regionserver had err and stop
2. [TTransportException(message='TSocket read 0 bytes', type=4)]
maybe thrift had stop or err
3. [Errno 32] Broken pipe
maybe thrift restart after err
4. [Missing Result]
thrift restart bug socket still usable
"""

def retry_five(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        for i in xrange(5):
            try:
                return fn(self, *args, **kwargs)
            except (TException, socket.error) as e:
                second = 3 << (i % 4)  # sleep 3, 6, 12,
                logger.error( "func[{}] had err:[{}], retry times:{}, sleep {}s".format(fn.__name__, e, i, second))
                time.sleep(second)
            except OperationalError as e:
                # Fix bug: (2006, 'MySQL server has gone away')
                # https://code.djangoproject.com/ticket/21597#comment:29
                logger.error( "func[{}] had mysql_error:[{}], retry times:{}, sleep 3s".format(fn.__name__, e, i))
                time.sleep(3)
            except Exception as e:
                logger.exception(
                    "func[{}] had error:[{}], args:{}".
                    format(fn.__name__, e, args)
                )
                raise e
        raise e
    return wrapper


def retry(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        timer = 0
        while True:
            try:
                return fn(self, *args, **kwargs)
            except (TException, socket.error) as e:
                second = 3 << (timer % 4)  # sleep 3, 6, 12, 24s
                timer += 1
                logger.error( "func[{}] had err:[{}], retry times:{}, sleep {}s".format(fn.__name__, e, timer, second))
                time.sleep(second)
            except OperationalError as e:
                timer += 1
                # Fix bug: (2006, 'MySQL server has gone away')
                # https://code.djangoproject.com/ticket/21597#comment:29
                logger.error( "func[{}] had mysql_error:[{}], retry times:{}, sleep 3s".format(fn.__name__, e, timer))
                connection.close()
                time.sleep(3)
            except Exception as e:
                logger.exception(
                    "func[{}] had error:[{}], args:{}".
                    format(fn.__name__, e, args)
                )
                raise e
            else:
                # 重置失败次数
                timer = 0
        raise e
    return wrapper
