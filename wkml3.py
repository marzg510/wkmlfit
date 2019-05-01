# coding: utf-8

import logging,logging.handlers
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import datetime
from IPython.display import Image,display_png
#from oauth2client import client
#from apiclient.discovery import build
#from oauth2client.file import Storage
import json,re
#import werkzeug

OUTDIR_SS='./file/ss/'
LOGDIR='./log/'

def ss(driver,seq,name=None):
    '''
    スクリーンショットを撮る
    '''
    add_name = 'ss' #if name is None else name
    fname = '{}/{}_{}.png'.format(OUTDIR_SS,seq,add_name)
    log.debug("ss fname ={}".format(fname))
    driver.get_screenshot_as_file(fname)

def lambda_handler(event, context):
    log.info("start")
    # ConfigFile読み込み
    with open('config.json', 'r') as f:
        conf = json.load(f)
    # ブラウザを起動
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=options)
    driver.set_page_load_timeout(5)
    # 入力画面を表示
    log.info("getting top page")
    driver.get('https://pepup.life/scsk_mileage_campaigns')
    ss(driver,1)
    # ログイン
    log.info("logging in to the site...")
    e_user = driver.find_element_by_id('sender-email')
    e_password = driver.find_element_by_id('user-pass')
    e_user.send_keys(conf['user'])
    e_password.send_keys(conf['password'])
    e_button = driver.find_element_by_name('commit')
    e_button.click()
    ss(driver,2)

    # ボタンの一覧
#    for b in driver.find_elements_by_tag_name('button'):
#    for b in driver.find_elements_by_xpath('//button[matches(text(),"[0-9]*")]'):
#    for b in driver.find_elements_by_xpath('//button[not(text()="")]'):
#        log.debug('buttons:name={},id={},type={},class={},text={},is_disped={},is_enabled={}'.format(b.get_attribute('name'),b.get_attribute('id'),b.get_attribute('type'),b.get_attribute('class'),b.text,b.is_displayed(),b.is_enabled()))

    # 未入力の日付ボタンのclassを取得
    b = driver.find_elements_by_tag_name('button')[-2]
    log.debug('last button:name={},id={},type={},class={},text={},is_disped={},is_enabled={}'.format(b.get_attribute('name'),b.get_attribute('id'),b.get_attribute('type'),b.get_attribute('class'),b.text,b.is_displayed(),b.is_enabled()))
    c = b.get_attribute('class')
    # 押せるボタンがなくなるまで、ボタンを一つづつ押して記録
    is_recorded = True
    seq = 3
    while is_recorded:
        is_recorded = record_one(driver,c)
        log.info('recorded:{}'.format(is_recorded))
        ss(driver,seq)
        seq += 1

    driver.quit()
    log.info("end")

def record_one(driver, class_str):
    '''
    画面から未入力のボタンを取得し、最初のボタンに該当する項目だけを記録
    '''
    # 未入力のボタンを取得
    log.info('finding pushable buttons..')
    buttons = driver.find_elements_by_xpath("//*[@class='{}']".format(class_str))
    # ボタンを一つづつ押して記録
    is_recorded = False
    for b in buttons:
        b.click()
        rec_btn = driver.find_element_by_xpath("//button[text()='記録']")
        can_btn = driver.find_element_by_xpath("//button[text()='キャンセル']")
        dt = driver.find_element_by_xpath("//div[text()='記録']/following-sibling::div")
        dtext = re.match('^\d+年\d+月\d+日', dt.text).group()
        # 日付が今日以降ならスキップ
        is_past = (datetime.datetime.strptime(dtext,"%Y年%m月%d日") < datetime.datetime(*datetime.date.today().timetuple()[:3]))
        log.debug("date={},past?={}".format(dtext,is_past))
        if is_past == False:
            log.info('skip date:{}(past)'.format(dtext))
            can_btn.click()
            continue
        if dt.text.find('この日の歩数を入力してください') > 0:
            inp = driver.find_element_by_xpath("//input[@name='vitalInput']")
            import random
            step = random.randint(5000,10000)
            inp.send_keys(step)
            log.info('歩数:{}'.format(step))
        elif dt.text.find('睡眠時間を入力してください') > 0:
            inp = driver.find_element_by_xpath("//input[@name='vitalInput']")
            sleep = 7
            inp.send_keys(sleep)
            log.info('睡眠時間:{}'.format(sleep))
        else:
            log.debug('checkbox')
            checkboxes = driver.find_elements_by_xpath("//input[@type='checkbox']")
            for c in checkboxes:
                c.click()
                log.info('checkbox:{}'.format(c.find_element_by_xpath('..').text))
        rec_btn.click()
        time.sleep(3)
#        can_btn.click()
        is_recorded = True
        break
    return is_recorded

if __name__ == '__main__':
    log = logging.getLogger('wkml3')
    log.setLevel(logging.DEBUG)
#    h = logging.StreamHandler()
    h = logging.handlers.TimedRotatingFileHandler('{}/wkml3.log'.format(LOGDIR),'M',1,13)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    log.addHandler(h)
    lambda_handler( {}, {} )

