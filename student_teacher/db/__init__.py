import MySQLdb
import logging

logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(module)s - %(message)s",
    level=logging.DEBUG,
)

# Init database
DB_CON = MySQLdb.connect(
    host="localhost", user="admin", password="password", database="school_db"
)

# Max size when fetchmany
MAX_SIZE = 1_000_000
