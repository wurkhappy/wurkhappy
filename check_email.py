# Check for new signups

from controllers.orm import Database
from controllers.email import Email
from models.user import User, UserPrefs
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
		query = """SELECT u.* FROM {0} AS u WHERE id NOT IN (
			SELECT p.id FROM {1} AS p WHERE name = 'userSignupAcknowledged'
		)""".format(User.tableName, UserPrefs.tableName)
		
		cursor.execute(query)
		newUsers.extend(User.initWithDict(x) for x in cursor.fetchall())
		
		query = "INSERT INTO {0} (userID, name, value) VALUES (%s, %s, %s)".format(User.tableName)
		cursor.executemany(query, [(user['id'], 'userSignupAcknowledged', True) for user in newUsers])
		
		conn.commit()
	
	if len(newUsers) > 0:
		subject = "New sign-ups"
		msgString = "The following people requested more information:\n\n%s" % "\n".join(user['email'] for user in newUsers)

		Email.sendmail('contact@wurkhappy.com', 'Subscription Manager', 'contact@wurkhappy.com', subject, msgString)