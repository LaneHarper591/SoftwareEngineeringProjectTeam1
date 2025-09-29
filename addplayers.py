import psycopg2

from pygame.locals import*
from time import sleep
from psycopg2 import sql

# Creating Required SQL DB connections
connection_params = {
	'dbname': 'photon',
  	'user': 'student',
	}

conn = psycopg2.connect(**connection_params)
cursor = conn.cursor()

# Add two additional players to database if not already in database
# Enter id and code name into database
sql_query = "INSERT INTO players (id, codename) VALUES (%s, %s);"
cursor.execute(sql_query, (2, "Shark"))
conn.commit()
# Enter id and code name into database
sql_query = "INSERT INTO players (id, codename) VALUES (%s, %s);"
cursor.execute(sql_query, (3, "Lazer"))
conn.commit()

conn.close()
cursor.close()