# A Simple Object Relational Mapper
# 
# created by Brendan Berg
# copyright 2009, Plus or Minus Five
# 
# For documentation and instructions, visit 
# http://github.com/brendn/webster

import MySQLdb
import json


# -------------------------------------------------------------------
# Database Wrappers & Somesuch
# -------------------------------------------------------------------

class DatabaseConnectionError(Exception):
	pass

class Database(object):
	settings = {}
	
	@classmethod
	def configure(clz, settings, mode = None):
		clz.settings[mode] = settings
	
	def __init__(self, mode=None):
		if mode and mode not in self.settings:
			self._mode = None
		self._mode = mode
	
	def __enter__(self):
		if self._mode not in self.settings:
			raise DatabaseConnectionError('database not configured')
		self._conn = MySQLdb.connect(**self.settings[self._mode])
		self._cursor = self._conn.cursor(MySQLdb.cursors.DictCursor)
		return (self._conn, self._cursor)
	
	def __exit__(self, type, value, traceback):
		self._cursor.close()
		self._conn.close()


# -------------------------------------------------------------------
# Simple Object <-> Relational Mapper
# -------------------------------------------------------------------

class MappedObj(object):
	tableName = ''
	columnNames = ['id']
	
	@classmethod
	def initWithDict(clz, dictionary):
		if not isinstance(dictionary, dict): return None
		
		instance = clz()
		for key, value in dictionary.iteritems():
			instance.__dict__[key] = value
		return instance
	
	@classmethod
	def retrieveByID(clz, uid):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE id = %%s LIMIT 1" % clz.tableName(), uid)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)
	
	
	
	def __init__(self):
		for name in self.columnNames:
			self.__dict__[name] = None
	
	def immutableFields(self):
		return ['id']
	
	def save(self):
		with Database() as (conn, cursor):
			cursor = conn.cursor(MySQLdb.cursors.DictCursor)
		
			keys = []
			values = []
		
			for k, v in self.__dict__.iteritems():
				if k != 'id':
				#if k not in self.immutableFields():
					keys += [k]
					values += [v]
		
			if self.id:
				values += [self.id]
			
				atom = "%s = %%s"
				setClause = ", ".join([atom] * len(keys))
				setClause = setClause % tuple(keys)
			
				updateStatement = "UPDATE %s SET %s WHERE id = %%s LIMIT 1" % (self.tableName(), setClause)
			
				#print setClause + "\n"
				#print updateStatement + "\n"
			
				cursor.execute(updateStatement, tuple(values))
				conn.commit()
			else:
				atom = "%s"
			
				keyClause = ", ".join(keys)
				valueClause = ", ".join([atom] * len(keys))
			
				#print keyClause + "\n"
				#print valueClause + "\n"
			
				insertStatement = "INSERT INTO %s (%s) VALUES (%s)" % (self.tableName(), keyClause, valueClause)
				cursor.execute(insertStatement, tuple(values))
				self.id = cursor.lastrowid
			
				conn.commit()
	
	def getPublicDictionary(self):
		return {}
	
	def __repr__(self):
		return json.encode(self.__dict__)
	