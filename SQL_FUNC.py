import pyodbc
import threading
import datetime


class SQL:

    def __init__(self):
        server = 'XXXXXXX'
        database = 'XXXXXXX'
        username = 'XXXXXXX'
        password = r'XXXXXXX'

        self.conn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

        self.sem = threading.Semaphore()

    def query_sql(self, query):
        self.sem.acquire()

        cursor = self.conn.cursor()
        cursor.execute(query)

        output = cursor.fetchall()
        cursor.close()

        self.sem.release()

        return output

    def reset_all_active_user_wax(self):
        self.sem.acquire()

        cursor = self.conn.cursor()

        execProcSql = """\
        EXEC TLM.Reset_All_Active_Users
        """

        cursor.execute(execProcSql, ())
        self.conn.commit()
        cursor.close()

        self.sem.release()

    def get_acct_info(self, wid):
        self.sem.acquire()

        cursor = self.conn.cursor()

        query = "SELECT WalletID, Email, EmailPass, WaxPass,  ProxyIP, ProxyPort, ProxyUser, ProxyPass FROM TLM.Acct_Details_D " \
                "WHERE " \
                "WalletID = '" + wid + "' "

        cursor.execute(query)
        output = cursor.fetchall()
        cursor.close()

        outputDic = {
            'WalletID': output[0][0],
            'Email': output[0][1],
            'EmailPass': output[0][2],
            'WaxPass': output[0][3],
            'ProxyIP': output[0][4],
            'ProxyPort': output[0][5],
            'ProxyUser': output[0][6],
            'ProxyPass': output[0][7]
        }

        self.sem.release()

        return outputDic

    def get_batch_end(self, wid):
        self.sem.acquire()

        cursor = self.conn.cursor()

        query = "SELECT Batch_End FROM [TLM].[Acct_Stats_D] " \
                "WHERE " \
                "WalletID = '" + wid + "' "

        cursor.execute(query)
        output = cursor.fetchall()
        cursor.close()

        batch_end = output[0][0]

        self.sem.release()

        return batch_end


    def get_out_of_resource(self, wid):
        self.sem.acquire()

        cursor = self.conn.cursor()

        query = "SELECT Out_Of_Resource FROM [TLM].[Acct_Stats_D] " \
                "WHERE " \
                "WalletID = '" + wid + "' "

        cursor.execute(query)
        output = cursor.fetchall()
        cursor.close()

        batch_end = output[0][0]

        self.sem.release()

        return batch_end

    def get_inactive_user_wax(self):
        self.sem.acquire()

        cursor = self.conn.cursor()

        exec_proc_sql = """\
        DECLARE @PY_OUT nvarchar(MAX)
        EXEC dbo.Get_Inactive_User_Wax @out = @PY_OUT OUTPUT
        SELECT @PY_OUT
        """

        cursor.execute(exec_proc_sql, ())
        output = cursor.fetchval()
        self.conn.commit()
        cursor.close()

        self.sem.release()

        return output

    def get_inactive_user(self, wid):
        self.sem.acquire()

        cursor = self.conn.cursor()
        execProcSql = "EXEC TLM.Get_Inactive_User @id = '" + wid + "'"
        cursor.execute(execProcSql, ())
        self.conn.commit()
        cursor.close()

        self.sem.release()

    def insert_batch_mine(self, wid, cd):
        self.sem.acquire()

        cursor = self.conn.cursor()
        execProcSql = "EXEC [TLM].[Insert_Batch_Mine] @id = '" + wid + "' , @CD = '" + cd + "'"
        cursor.execute(execProcSql, ())
        self.conn.commit()
        cursor.close()

        self.sem.release()

    def return_active_user(self, wid):
        self.sem.acquire()

        cursor = self.conn.cursor()
        execProcSql = "EXEC [TLM].[Return_Active_User] @id = '" + wid + "'"
        cursor.execute(execProcSql, ())
        self.conn.commit()
        cursor.close()

        self.sem.release()

    def queue_active_user(self, wid):
        self.sem.acquire()

        cursor = self.conn.cursor()
        execProcSql = "EXEC [TLM].[Queue_Active_User] @id = '" + wid + "'"
        cursor.execute(execProcSql, ())
        self.conn.commit()
        cursor.close()

        self.sem.release()

    def dequeue_active_user(self, wid):
        self.sem.acquire()

        cursor = self.conn.cursor()
        execProcSql = "EXEC [TLM].[dequeue_Active_User] @id = '" + wid + "'"
        cursor.execute(execProcSql, ())
        self.conn.commit()
        cursor.close()

        self.sem.release()

    def set_ran_out_of_resource(self, wid):
        self.sem.acquire()

        cursor = self.conn.cursor()
        execProcSql = "EXEC [TLM].[Set_Out_Of_Resource] @id = '" + wid + "'"
        cursor.execute(execProcSql, ())
        self.conn.commit()
        cursor.close()

        self.sem.release()

    def start_run_batch(self, wid, cb):
        self.sem.acquire()

        cursor = self.conn.cursor()
        execProcSql = "EXEC TLM.Start_Run_Batch @id = '" + wid + "', @C_B = '" + cb + "'"
        cursor.execute(execProcSql, ())
        self.conn.commit()
        cursor.close()

        self.sem.release()

    def insert_mine(self, walletid, uid, deltaamt, curramt):
        insert = "INSERT INTO TLM.Acct_Mining_F (WalletID, Instance, Mined, Total, [DateTime])VALUES ( '" + walletid + "', '" + uid + "'," + str(
            deltaamt) + "," + str(curramt) + ",'" + str(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")) + "');"

        self.sem.acquire()

        cursor = self.conn.cursor()
        cursor.execute(insert)

        self.conn.commit()
        cursor.close()

        self.sem.release()
