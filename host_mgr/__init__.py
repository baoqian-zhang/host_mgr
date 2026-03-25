import pymysql

from host_mgr.tasks import app

pymysql.install_as_MySQLdb()
__all__ = ('app',)
