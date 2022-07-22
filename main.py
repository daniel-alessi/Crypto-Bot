import concurrent.futures
import time
from SQL_FUNC import SQL as sq
import SELENIUM_FUNC as sl
import pandas as pd
import traceback
import sys
import os
import uuid
import warnings
from datetime import datetime

warnings.simplefilter(action='ignore', category=UserWarning)


def run_bot(acct):
    sql_instance = sq()
    failed = False

    ip_port = acct['ProxyIP'] + ':' + acct['ProxyPort']
    driver = sl.setup_driver('downloads', ip_port, testmode=True)
    driver_wait = sl.setup_webdriver(driver, 15)

    try:

        sl.login(acct['Email'], acct['WaxPass'], acct['EmailPass'], driver, driver_wait)
        exitcode, details = sl.mine_one(acct['WalletID'], driver, driver_wait)
        driver.close()

    except Exception as e:

        sql_instance.dequeue_active_user(acct['WalletID'])

        top = traceback.extract_tb(sys.exc_info()[2])[-1]
        driver.close()
        detail = '{} : {} in {} at line {}'.format(type(e).__name__, str(e), os.path.basename(top[0]), str(top[1]))
        print('failed at selenium code')
        print(detail)
        failed = True

    if not failed:

        try:

            if exitcode == 'OOM':

                if details > 100:
                    sql_instance.set_ran_out_of_resource(acct['WalletID'])

            else:

                # insert batch mine
                sql_instance.insert_batch_mine(acct['WalletID'], '00:08:00')

                # track mining metrics
                sql_instance.insert_mine(acct['WalletID'], acct['batch'], details[0], details[1])

        except Exception as e:

            top = traceback.extract_tb(sys.exc_info()[2])[-1]
            detail = '{} : {} in {} at line {}'.format(type(e).__name__, str(e), os.path.basename(top[0]), str(top[1]))
            print('failed to track metrics')
            print(detail)

    try:

        # dequeue acct
        sql_instance.dequeue_active_user(acct['WalletID'])

    except Exception as e:

        top = traceback.extract_tb(sys.exc_info()[2])[-1]
        detail = '{} : {} in {} at line {}'.format(type(e).__name__, str(e), os.path.basename(top[0]), str(top[1]))
        print('failed to dequeue')
        print(detail)


if __name__ == '__main__':

    sql_obj = sq()

    batchs = {}

    sql_obj.reset_all_active_user_wax()

    with concurrent.futures.ProcessPoolExecutor(3) as executor:

        while True:

            try:

                # add available inactive users to the batch
                sql = 'SELECT * FROM [TLM].[Avalible_Inactive_Users]'
                df = pd.read_sql(sql, sql_obj.conn)

                for index, row in df.iterrows():
                    # set the user to active
                    sql_obj.get_inactive_user(row['WalletID'])

                    acct = sql_obj.get_acct_info(row['WalletID'])
                    acct['batch'] = str(uuid.uuid4())
                    acct['mine_attempt'] = 0

                    sql_obj.start_run_batch(acct['WalletID'], acct['batch'])

                    batchs[acct['WalletID']] = acct

                # get available active users
                sql = 'SELECT * FROM [TLM].[Avalible_Active_Users] order by Next_Mine asc'
                df = pd.read_sql(sql, sql_obj.conn)

                queue = []

                # for each active user
                for index, row in df.iterrows():

                    # pop expired batches
                    batch_end = sql_obj.get_batch_end(row['WalletID'])
                    if batch_end < datetime.now():
                        sql_obj.return_active_user(row['WalletID'])
                        batchs.pop(row['WalletID'])
                        continue

                    # pop OOM batches
                    resource = sql_obj.get_out_of_resource(row['WalletID'])
                    if resource:
                        sql_obj.return_active_user(row['WalletID'])
                        batchs.pop(row['WalletID'])
                        continue

                    # queue ready accounts
                    queue.append(batchs[row['WalletID']])
                    sql_obj.queue_active_user(row['WalletID'])

                # execute queued items
                results = executor.map(run_bot, queue)

                time.sleep(3)

                # print items in the current batch
                for key, value in batchs.items():
                    print(key, ' : ', value)

            except Exception as e:

                top = traceback.extract_tb(sys.exc_info()[2])[-1]
                detail = '{} : {} in {} at line {}'.format(type(e).__name__, str(e), os.path.basename(top[0]),
                                                           str(top[1]))
                print('failed to dequeue')
                print(detail)
