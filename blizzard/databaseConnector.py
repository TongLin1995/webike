from __future__ import division 
import pymysql as MySQLdb

#only need one instance of this connector to manage all database calls
class databaseConnector(object):
    def __init__(self, app):
        try:    
            #now go open that conf file and get the username and password
            for line in open(app.config["DB_CREDENTIALS_PATH"]).readlines():
                items = line.split(" := ")
                if items[0].strip() == "passwd":
                    p = items[1].strip().split("\"")[1].split("\"")[0]
                if items[0].strip() == "user":
                    usr = items[1].strip() 
            self.myDB = MySQLdb.connect(host=app.config["DB_HOST"], port=3306, user=usr,passwd='{0}'.format(p), db=app.config["DB_NAME"])
            #http://legacy.python.org/dev/peps/pep-0249/#id7
            self.cur = self.myDB.cursor() 
        except MySQLdb.Error as msg:
            print("MYSQL ERROR!")
            print(msg)
    
    def shutDown(self):
        self.cur.close() #close the cursor  
        self.myDB.close()
    
    #execute a select query and return results as a generator
    def SQLSelectGenerator(self,stmt):
        #print("Executing: " + stmt)    
        try:
            self.cur.execute(stmt)
        except MySQLdb.Error as msg:
            print("MYSQL ERROR: {0}".format(msg))
                
        data = self.cur.fetchall()
        for row in data:
            yield row
            
        #TO DO ONE AT A TIME:
        """row = ""
        while row is not None:
            row = self.cur.fetchone()
            yield row
            
        #this also seems to be valid though it is cryptic:
        for row in self.cur:
            yield row"""
        
                
    #execute a bunch of sql queries 
    def SQLExecQueryQueue(self, Q):
        for q in Q:
            try: 
                self.cur.execute(q)
            except MySQLdb.Error as msg:
                print("MYSQL ERROR!:{0}".format(msg)) #print error but keep going
        self.myDB.commit()           
 
    #exectute a single query
    def SQLExecQuery(self,stmt):
        try:    
            print(stmt)
            self.cur.execute(stmt)
            self.myDB.commit()
        except MySQLdb.Error as msg:
            print("MYSQL ERROR!")
            print(msg) 
                      



