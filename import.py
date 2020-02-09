import os
import csv

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for DATABASE_URL variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
md = MetaData()
print('database connected')

# find all csv files within the directory
for file in os.listdir('./'):
    if file.endswith('.csv'):
        tablename = os.path.splitext(file)[0]  # get name of table from file
        # get table primary key from database
        table = Table(tablename, md, autoload=True, autoload_with=engine)
        primaryKeyColName = str(table.primary_key.columns.values()[0].name)
        # types = []
        # i = 0
        # for c in table.c:
        #     types.append(c.type.python_type)

        f = open(file, "r")  # open file
        nrows = sum(1 for row in f)  # get number of rows
        f = open(file, "r")  # reopen file
        reader = csv.reader(f)

        line = -1
        for row in reader:
            line += 1

            if (line % 100) == 0:
                print("Progress: %(percent)s%%" % {'percent': line / nrows * 100})
            # at first row (assuming csv contains headings)
            if line == 0:
                colnames = row  # get column names from csv
                continue

            # construct INSERT SQL command from csv
            commandbein = 'INSERT INTO %(tablename)s (' % {'tablename': tablename}
            commandend = ' VALUES ('
            colcount = 0
            rowexists = False
            for value in row:
                # if the value is the primary key
                if colnames[colcount] == primaryKeyColName:
                    # check if primary key already exists in database
                    command = "SELECT COUNT(%(primaryKeyColName)s) FROM %(tablename)s WHERE %(primaryKeyColName)s='%(value)s'" % {
                        'primaryKeyColName': primaryKeyColName, 'tablename': tablename, 'value': value}
                    num = db.execute(command).fetchall()
                    if num[0][0] > 0:
                        print("Skipping row: " + str(row) + " as it already exists in database")
                        rowexists = True
                        break
                # escape ' character by replacing with ''
                if "'" in value:
                    value = value.replace("'", "''")

                commandbein += '%(colname)s, ' % {'colname': colnames[colcount]}
                commandend += "'%(value)s', " % {'value': value}
                colcount += 1
            if rowexists: continue
            commandbein = commandbein[0:len(commandbein) - 2] + ') '
            commandend = commandend[0:len(commandend) - 2] + ')'
            command = commandbein + commandend
            db.execute(command)
            #print(row)
        db.commit()
