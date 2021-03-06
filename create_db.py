import sqlite3
from sqlite3 import Error
import string
import pickle
database = r"firebase.db"

def create_table(conn, create_table_sql):
	try:
		c = conn.cursor()
		c.execute(create_table_sql)
	except Error as e:
		print(e)
def create_connection(db_file):
	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)
	return conn

def create_state(conn, state):
	if check_state(conn,state):
		return False
	cur = conn.cursor()
	sql = ''' INSERT INTO information(state) VALUES(?) '''
	cur.execute(sql, (state,))
	conn.commit()
	return cur.rowcount >=1
def check_state(conn,state):
	cur = conn.cursor()
	cur.execute("SELECT state FROM information WHERE state = ?", (state,))
	data=cur.fetchall()
	return len(data)>0
def clear_latest(conn):
	cur = conn.cursor()
	cur.execute('''DELETE FROM latest;''')
	cur.execute('''DELETE FROM report;''')
	cur.execute('''DELETE FROM news;''')
	conn.commit()
# def update_total(conn,cases,cured,death):
	# cur=conn.cursor()
	# sql = ''' INSERT INTO latest(state,cases,cured,death) VALUES(?,?,?,?) '''
	# cur.execute(sql, ('total',cases,cured,death))
	# conn.commit()
def update_state(conn,state,cases,cured,death):
	cur = conn.cursor()
	state=state.lower()
	if not check_state(conn,state):
		sql = ''' INSERT INTO information(state) VALUES(?) '''
		cur.execute(sql, (state,))
	sdata=fetch_state(state)
	pcases=int(cases)-int(sdata['cases'])
	pcured=int(cured)-int(sdata['cured'])
	pdeath=int(death)-int(sdata['death'])
	if pcases==0 and pcured==0 and pdeath==0:
		conn.commit()
		return False
	sql = ''' INSERT INTO latest(state,cases,cured,death) VALUES(?,?,?,?) '''
	cur.execute(sql, (state,pcases,pcured,pdeath))
	sql = '''UPDATE information SET cases = ? , cured = ? , death = ? WHERE state =? '''
	cur.execute(sql, (cases,cured,death,state))
	conn.commit()
def update_news(title,link):
	conn=create_connection(database)
	cur = conn.cursor()
	sql = ''' INSERT INTO news(title,link) VALUES(?,?) '''
	cur.execute(sql, (title,link))
	conn.commit()
	return cur.rowcount >=1
def gen_new_report(totaldata):
# def gen_new_report():
	conn=create_connection(database)
	cur = conn.cursor()
	cur.execute('''SELECT state,cases,cured,death FROM latest; ''')
	data=cur.fetchall()
	full=[]
	suffix=[" new positive cases has been reported in "," people successfully cured of corona in "," people reported death by corona in "]
	for row in data:
		semi=[]
		for cell in range(1,4):
			if row[cell]!=0:
				semi.append(str(row[cell])+suffix[cell-1]+string.capwords(str(row[0])))
		full.append("\n".join(semi))
	fullreport="\n".join(full)
	cur.execute('''SELECT sum(cases),sum(cured),sum(death) FROM information; ''')
	# data=cur.fetchall()[0]
	data=totaldata
	sql = ''' INSERT INTO report(casereport,cases,cured,death) VALUES(?,?,?,?) '''
	cur.execute(sql, (fullreport,data[0],data[1],data[2]))
	conn.commit()
	return cur.rowcount >=1
def fetch_state(state):
	conn=create_connection(database)
	state=state.lower()
	sql = '''SELECT cases,cured,death FROM information WHERE state = ? '''
	cur = conn.cursor()
	cur.execute(sql, (state,))
	try:
		data=cur.fetchall()[0]
		return {"cases":data[0],"cured":data[1],"death":data[2]}
	except:
		return {"cases":0,"cured":0,"death":0}
def fetch_all():
	conn=create_connection(database)
	cur = conn.cursor()
	cur.execute('''SELECT state,cases,cured,death FROM information ;''')
	data=cur.fetchall()
	full=[]
	try:
		for row in data:
			full.append({"state":row[0],"cases":row[1],"cured":row[2],"death":row[3]})
		return {"all":full}
	except:
		return {"status":"failed"}
def fetch_news():
	conn=create_connection(database)
	cur = conn.cursor()
	cur.execute('''SELECT title,link,time FROM news; ''')
	data=cur.fetchall()
	result=[]
	try:
		for d in data:
			result.append({"title":d[0],"link":d[1],"time":d[2]})
		return {"news":result}
	except:
		return {"status":"failed"}
def fetch_report():
	conn=create_connection(database)
	cur = conn.cursor()
	cur.execute('''SELECT casereport FROM report; ''')
	data=cur.fetchall()
	cur.execute('''SELECT sum(cases),sum(cured),sum(death) FROM latest; ''')
	# cur.execute('''SELECT cases,cured,death FROM latest WHERE state = 'total'; ''')
	response={"cases":0,"cured":0,"death":0}
	try:
		with open('data.dump', 'rb') as handle:
			olddata = pickle.load(handle)
	except:
		olddata={"cases":0,"cured":0,"death":0}
	try:
		alldata=cur.fetchall()[0]
		for i,key in enumerate(response):
			response[key]=alldata[i] if not alldata[i] is None else 0
	except:
		response={"cases":0,"cured":0,"death":0}
	
	for i,key in enumerate(response):
		response[key]=olddata[key] if response[key]==0 else response[key]	
	try:
		response["report"]=data[0][0]
	except:
		response["report"]=""
	return response
def fetch_total():
	conn=create_connection(database)
	cur = conn.cursor()
	cur.execute('''SELECT cases,cured,death FROM report; ''')
	try:
		data=cur.fetchall()[0]
		return {"cases":data[0],"cured":data[1],"death":data[2],"hospitalized":(int(data[0])-int(data[1])-int(data[2]))}
	except:
		return {"cases":0,"cured":0,"death":0,"hospitalized":0}
def predict(state):
	conn=create_connection(database)
	lcases=fetch_state(state)['cases']
	tcases=fetch_total()['cases']
	cur = conn.cursor()
	cur.execute('''SELECT max(cases) FROM information; ''')
	data=int(cur.fetchall()[0][0])
	tcases=(data+tcases)/2.0	
	probability=(lcases*100.0)/tcases
	return {"probability":probability}
def main():
	sql_create_info_table = """ CREATE TABLE IF NOT EXISTS information (
										id integer PRIMARY KEY,
										state text NOT NULL,
										cases number DEFAULT 0,
										cured number DEFAULT 0,
										death number DEFAULT 0
									); """
	sql_create_update_table = """ CREATE TABLE IF NOT EXISTS latest (
										id integer PRIMARY KEY,
										state text NOT NULL,
										cases number DEFAULT 0,
										cured number DEFAULT 0,
										death number DEFAULT 0
									); """
	sql_create_report_table = """ CREATE TABLE IF NOT EXISTS report (
										id integer PRIMARY KEY,
										casereport text DEFAULT "",
										cases number DEFAULT 0,
										cured number DEFAULT 0,
										death number DEFAULT 0
									); """
	sql_create_news_table = """ CREATE TABLE IF NOT EXISTS news (
										id integer PRIMARY KEY,
										title text DEFAULT "",
										link text DEFAULT "",
										time DATE DEFAULT (datetime('now','localtime'))
									); """
	# create a database connection
	conn = create_connection(database)
 
	# create tables
	if conn is not None:
		# create projects table
		create_table(conn, sql_create_info_table)
		create_table(conn, sql_create_update_table)
		create_table(conn, sql_create_report_table)
		create_table(conn, sql_create_news_table)
 
	else:
		print("Error! cannot create the database connection.")

main()