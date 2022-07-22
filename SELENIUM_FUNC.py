from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
import time
import LIB as lib
from SQL_FUNC import SQL as sq
import uuid
import re


def setup_driver(download_path, proxy_ip_port, testmode=True):
    # driver options

    options = webdriver.ChromeOptions()

    if not testmode:
        options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')

        user_agent = r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 ' \
                     r'Safari/537.36 '
        options.add_argument(f'user-agent={user_agent}')

    options.add_argument('--incognito')

    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.HTTP_proxy = proxy_ip_port
    proxy.ssl_proxy = proxy_ip_port

    capabilities = webdriver.DesiredCapabilities.CHROME
    proxy.add_to_capabilities(capabilities)

    driver_path = r"C:\Users\danie\PycharmProjects\TLM_BOT\chromedriver.exe"

    return webdriver.Chrome(driver_path, options=options, desired_capabilities=capabilities)


def setup_webdriver(driver, tim):
    return WebDriverWait(driver, tim)


def switch_window_by_url(driver, url):
    found = False
    timeout = 0
    while not found:

        timeout += 1

        if timeout > 100:
            raise Exception("ERROR : switch_window_by_url : " + url)

        handles = driver.window_handles
        size = len(handles)

        for x in range(size):

            driver.switch_to.window(handles[x])
            time.sleep(0.1)

            if driver.current_url == url:
                found = True
                time.sleep(1)
                break


def get_urls(driver):
    urls = []

    handles = driver.window_handles
    size = len(handles)

    for x in range(size):
        driver.switch_to.window(handles[x])
        time.sleep(0.1)
        urls.append(driver.current_url)

    return urls


def get_url_index(listt, string):
    for i in range(len(listt)):
        if listt[i].find(string) != -1:
            return i

    return None


def verify_account(driver, driverwait, user, pasw):
    urls = get_urls(driver)

    for url in urls:

        if 'https://all-access.wax.io/challenge' in url:
            index = get_url_index(urls, 'https://all-access.wax.io/challenge')

            switch_window_by_url(driver, urls[index])

            verifcode = lib.get_email_verification(user, pasw)

            verif = driverwait.until(
                EC.element_to_be_clickable((By.XPATH, "//form[@class='signin-2fa-form']/div/div/input")))
            verif.clear()
            verif.send_keys(verifcode)

            driverwait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Continue']"))).click()


def wax_approve(driver, driverwait, url):
    timeout = 0
    while True:

        timeout += 1

        if timeout > 30:
            raise Exception("ERROR : wax_approve : " + url)

        switch_window_by_url(driver, url)
        approve = driverwait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Approve']")))
        driver.execute_script('arguments[0].click();', approve)
        time.sleep(1)

        handles = driver.window_handles
        size = len(handles)

        if url not in get_urls(driver):
            break


def wait_for_window_count(driver, count):
    timeout = 0
    while len(driver.window_handles) > count:

        timeout += 1

        if timeout > 30:
            raise Exception("ERROR : wait_for_window_count : " + count)

        time.sleep(1)


def login(user, pasw, pase, driver, driverwait):
    print(user)

    # GET-PAGE
    driver.get('https://play.alienworlds.io')

    # START-GAME
    driverwait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Start Now']"))).click()

    # SWITCH-WINDOWS
    switch_window_by_url(driver, r'https://all-access.wax.io/')

    # LOGIN
    username = driverwait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='userName']")))
    username.clear()
    username.send_keys(user)

    password = driverwait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='password']")))
    password.clear()
    password.send_keys(pasw)

    driverwait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']"))).click()

    time.sleep(10)

    verify_account(driver, driverwait, user, pase)

    # APPROVE-LOGIN
    wax_approve(driver, driverwait, r'https://all-access.wax.io/cloud-wallet/login/')

    # SWAP-TO-MINER
    wait_for_window_count(driver, 1)
    switch_window_by_url(driver, r'https://play.alienworlds.io/inventory')


def check_exists_by_xpath(driver, path):
    try:
        driver.find_element_by_xpath(path)
    except:
        return False
    return True


def can_mine(driver):
    if check_exists_by_xpath(driver, "//span[text()='Mine']"):
        return True
    return False


def attempt_mine(driverwait):
    driverwait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Mine']"))).click()


def get_resource_amount(driverwait):
    resource_amt = driverwait.until(
        EC.presence_of_element_located((By.XPATH, "//p[text()=' CPU ']/following-sibling::p[1]"))).text

    return int(re.subn('[ %]', '', resource_amt)[0])


def get_trillium_amt(driverwait, prev=None):
    if prev is None:
        return float(driverwait.until(
            EC.presence_of_element_located((By.XPATH, "//p[text()='Trilium Balance']/parent::div/p"))).text)

    checkcount = 0
    while True:
        checkcount += 1

        trilamt = driverwait.until(
            EC.presence_of_element_located((By.XPATH, "//p[text()='Trilium Balance']/parent::div/p"))).text

        time.sleep(1)
        if float(trilamt) != prev:
            break

        if checkcount >= 10:
            return -1

    return float(trilamt)


def can_claim(driver):
    if check_exists_by_xpath(driver, "//span[text()='Claim Mine']"):
        return True
    return False


def close_popup_windows(driver, url):
    handles = driver.window_handles
    size = len(handles)

    for x in reversed(range(size)):

        driver.switch_to.window(handles[x])
        time.sleep(0.1)
        if driver.current_url != url:
            driver.close()


def attempt_claim(driver, driverwait, url):
    try:

        driverwait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Claim Mine']"))).click()
        wax_approve(driver, driverwait, r'https://all-access.wax.io/cloud-wallet/signing/')

    except:

        close_popup_windows(driver, url)


def mine(walletid, driver, driverwait):
    sql_obj = sq()

    # MINE-LOOP
    uid = str(uuid.uuid4())
    start = time.time()
    startamt = get_trillium_amt(driverwait)
    minedamt = 0.0
    deltaamt = 0.0
    curramt = 0.0
    failcount = 0
    failtrys = 5

    print(f'Mining started!! | Start : %5.4f' % startamt)

    while True:

        if failcount > failtrys:
            return 'Ran Out Of Resource'

        if can_mine(driver):
            attempt_mine(driverwait)

        if can_claim(driver):

            curramt = get_trillium_amt(driverwait)

            attempt_claim(driver, driverwait, r'https://play.alienworlds.io/inventory')

            switch_window_by_url(driver, r'https://play.alienworlds.io/inventory')

            trilamt = get_trillium_amt(driverwait, curramt)

            if trilamt < 0:

                print('Mine FAILED!!')
                failcount += 1

            else:

                failcount = 0
                deltaamt = trilamt - curramt
                minedamt = trilamt - startamt
                elapsed = time.time() - start
                tril_hour = (minedamt / elapsed) * 3600

                print(
                    f"Mine Success!! | Mined : %5.4f | Delta : %5.4f | Current : %5.4f | Elapsed : %5.4f | Tril/Hr : "
                    f"%5.4f" % (
                        minedamt, deltaamt, curramt, (elapsed / 3600), tril_hour))

                sq.insert_mine(sql_obj, walletid, uid, deltaamt, curramt)

            time.sleep(3)


def mine_one(walletid, driver, driverwait):
    # MINE-LOOP
    startamt = get_trillium_amt(driverwait)
    failcount = 0
    failtrys = 5

    while True:

        if failcount > failtrys:

            resource_p = get_resource_amount(driverwait)

            return 'OOM', resource_p

        if can_mine(driver):
            attempt_mine(driverwait)

        if can_claim(driver):

            attempt_claim(driver, driverwait, r'https://play.alienworlds.io/inventory')

            switch_window_by_url(driver, r'https://play.alienworlds.io/inventory')

            curramt = get_trillium_amt(driverwait, startamt)

            if curramt < 0:

                failcount += 1

            else:

                failcount = 0

                minedamt = curramt - startamt

                return 'MINED', [minedamt, curramt]

            time.sleep(3)
