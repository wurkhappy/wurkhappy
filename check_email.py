# Check for new signups

from controllers.orm import Database
from controllers.email import Email
from models.user import User
import json
import yaml

if __name__ == "__main__":
	conf = yaml.load(open('_b.yaml', 'r'))
	
	Database.configure({
		"host": conf['database']['host'],
		"user": conf['database']['user'],
		"passwd": conf['database']['passwd'],
		"db": conf['database']['db']
	}, None)
	
	Email.configure(conf['smtp'])
	
	newUsers = []
	
	with Database() as (conn, cursor):
		query = "SELECT * FROM %s WHERE subscriberStatus = 0" % User.tableName()
		cursor.execute(query)
		
		newUsers.extend(User.initWithDict(x) for x in cursor.fetchall())
		
		query = "UPDATE %s SET subscriberStatus = 1 WHERE id = %%s" % User.tableName()
		cursor.executemany(query, [user['id'] for user in newUsers])
		conn.commit()
	
	if len(newUsers) > 0:
		subject = "New sign-ups"
		msgString = "The following people requested more information:\n\n%s" % "\n".join(user['email'] for user in newUsers)

		Email.sendmail('contact@wurkhappy.com', 'Subscription Manager', 'contact@wurkhappy.com', subject, msgString)