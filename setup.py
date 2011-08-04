from setuptools import setup

setup(
	name="wurkhappy",
	version="0.01a",
	description="Web Application for the Wurk Happy platform",
	
	install_requires=['tornado', 'MySQL-python', 'PyYAML >= 3.10']
)

print ""
print "MySQL-python has some path issues. Run `sudo ln -s /usr/local/mysql/lib/libmysqlclient.18.dylib /usr/lib/libmysqlclient.18.dylib` or appropriate alternative to resolve."