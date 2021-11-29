# coding: utf-8

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import time
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import json
import re
# from random_step import RandomStepGetter
from googlefit_step import GoogleFitStepGetter
import os
import sys
from selenium.webdriver.common.by import By

OUTDIR_SS = './file/ss/'
LOGDIR = './log/'
MAX_CLICKS = 31


def ss(driver, seq, name=None):
    '''
    スクリーンショットを撮る
    '''
    add_name = 'ss' if name is None else name
    fname = '{}/{}_{}.png'.format(OUTDIR_SS, seq, add_name)
    log.debug("ss fname ={}".format(fname))
    driver.get_screenshot_as_file(fname)
    ps(driver, seq, add_name)


def ps(driver, seq=None, name='ss'):
    '''
    HTMLソースを保存
    '''
    fname = os.path.join(OUTDIR_SS, '{}_{}.html'.format(seq, name))
    with open(fname, 'wt') as out:
        out.write(driver.page_source)
    return fname


def lambda_handler(event, context):
    log.info("start")
    # ConfigFile読み込み
    try:
        with open('config.json', 'r') as f:
            conf = json.load(f)
        # 歩数取得クラスの生成
    #    step_getter = RandomStepGetter(5000,10000)
        step_getter = GoogleFitStepGetter('./googlefit_credential',log)
        # ブラウザを起動
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(5)
        # 入力画面を表示
        log.info("getting top page")
        driver.get('https://pepup.life/scsk_mileage_campaigns')
        ss(driver, 1)
        # ログイン
        log.info("logging in to the site...")
        e_user = driver.find_element(By.ID,'sender-email')
        e_password = driver.find_element(By.ID,'user-pass')
        e_user.send_keys(conf['user'])
        e_password.send_keys(conf['password'])
        e_button = driver.find_element(By.NAME,'commit')
        e_button.click()
        ss(driver, 2)
        time.sleep(10)

        # ボタンの一覧
        for b in driver.find_elements(By.XPATH,'//button[not(text()="")]'):
            log.debug('buttons:name={},id={},type={},class={},text={},is_disped={},is_enabled={}'.format(b.get_attribute('name'), b.get_attribute('id'), b.get_attribute('type'), b.get_attribute('class'), b.text, b.is_displayed(), b.is_enabled()))

        # 未入力の日付ボタンのclassを取得
        log.info('Getting button class..')
        b = driver.find_elements(By.TAG_NAME,'button')[-1]
        log.debug('last button:name={},id={},type={},class={},text={},is_disped={},is_enabled={}'.format(b.get_attribute('name'),b.get_attribute('id'),b.get_attribute('type'),b.get_attribute('class'),b.text,b.is_displayed(),b.is_enabled()))
        c = b.get_attribute('class')
        log.info('button class={}'.format(b.get_attribute('class')))
        # 押せるボタンがなくなるまで、ボタンを一つづつ押して記録
        # 先月分のページを処理
        log.info('navigate to last month..')
        is_recorded = True
        seq = 3
        e = driver.find_element(By.XPATH,'//select[option[text()="過去の記録を見る"]]')
    #    log.debug('select-elem={}'.format(e))
        select_month = Select(e)
        last_month = date.today() - relativedelta(months=1)
        select_month.select_by_value('/scsk_mileage_campaigns/{}/{}'.format(last_month.year,last_month.month))
        time.sleep(5)
        ss(driver, seq)
        seq += 1
        log.info('recording..')
        click_cnt = 0
        while is_recorded:
            is_recorded = record_one(driver,c,step_getter)
            log.info('recorded:{}'.format(is_recorded))
            ss(driver,seq)
            seq += 1
            click_cnt += 1
            if click_cnt > MAX_CLICKS:   # 記録回数が一定回数を超えたらやめる
                log.warn('clicks over max({})'.format(MAX_CLICKS))
                break
        # 今月分のページを処理
        log.info('navigate to this month..')
        is_recorded = True
        e = driver.find_element(By.XPATH,'//select[option[text()="過去の記録を見る"]]')
        select_month = Select(e)
        this_month = date.today()
        select_month.select_by_value('/scsk_mileage_campaigns/{}/{}'.format(this_month.year,this_month.month))
        time.sleep(5)
        ss(driver, seq)
        seq += 1
        log.info('recording..')
        click_cnt = 0
        while is_recorded:
            is_recorded = record_one(driver, c, step_getter)
            log.info('recorded:{}'.format(is_recorded))
            ss(driver, seq)
            seq += 1
            click_cnt += 1
            if click_cnt > MAX_CLICKS:   # 記録回数が一定回数を超えたらやめる
                log.warn('clicks over max({})'.format(MAX_CLICKS))
                break

    except Exception as e:
        log.exception('exception occurred.')
        print(e, file=sys.stderr)

    finally:
        if (driver is not None):
            driver.quit()
            log.info("WebDriver Quit")
        log.info("end")


def record_one(driver, class_str, step_getter):
    '''
    画面から未入力のボタンを取得し、最初のボタンに該当する項目だけを記録
    '''
    # 未入力のボタンを取得
    log.debug('finding button class={}'.format(class_str))
    buttons = driver.find_elements(By.XPATH,"//*[@class='{}']".format(class_str))
    log.info('finding pushable buttons.. buttons = {}'.format(len(buttons)))
    # ボタンを一つづつ押して記録
    is_recorded = False
    for b in buttons:
        b.click()
        can_btn = driver.find_element(By.XPATH,"//button[text()='閉じる']")
        dt = driver.find_element(By.XPATH,"//div[text()='記録']/following-sibling::div")
        dtext = re.match('^\d+年\d+月\d+日', dt.text).group()
        # 日付が今日以降ならスキップ
        target_date = datetime.strptime(dtext,"%Y年%m月%d日")
        is_past = (target_date < datetime(*date.today().timetuple()[:3]))
        txt = re.sub('\n', '', dt.text)
        log.info("dialog text={},date={},past?={}".format(txt, dtext, is_past))
        if is_past is False:
            log.info('skip date:{}(not past)'.format(dtext))
            can_btn.click()
            continue
        if dt.text.find('歩以上') > 0:
            # 歩数入力
            inp = driver.find_element(By.XPATH,"//input[@name='vitalInput']")
            step = step_getter.get_step(target_date)
            log.info('歩数:{}'.format(step))
            if step <= 0:
                log.warning('skip date: because step <= 0')
                can_btn.click()
                continue
            inp.send_keys(step)
            rec_btn = driver.find_element(By.XPATH,"//button[text()='記録']")
            rec_btn.click()
        elif dt.text.find('睡眠時間を入力してください') > 0:
            # 睡眠時間記録
            inp = driver.find_element(By.XPATH,"//input[@name='vitalInput']")
            sleep = step_getter.get_sleep(target_date)
            log.debug('sleep : {}'.format(sleep))
            sleep = 7
            inp.send_keys(sleep)
            log.info('睡眠時間:{}'.format(sleep))
            rec_btn = driver.find_element(By.XPATH,"//button[text()='記録']")
            rec_btn.click()
        elif '記録日の気分を５段階でチェック' in dt.text:
            # 気分
            radios = driver.find_elements(By.XPATH,"//input[@type='radio']")
            for r in radios:
                if r.get_attribute('value') == 'normal':
                    r.click()
                    log.info('clicked radio:{}'.format(r.find_element(By.XPATH,'..').text))
                    rec_btn = driver.find_element(By.XPATH,"//button[text()='記録']")
                    rec_btn.click()
        elif '記録日の睡眠状態（よく眠れたか）' in dt.text:
            # 睡眠状態
            radios = driver.find_elements(By.XPATH,"//input[@type='radio']")
            for r in radios:
                if r.get_attribute('value') == 'bad':
                    r.click()
                    log.info('clicked radio:{}'.format(r.find_element(By.XPATH,'..').text))
                    rec_btn = driver.find_element(By.XPATH,"//button[text()='記録']")
                    rec_btn.click()
        else:
            log.debug('It is checkbox may be...')
            checkboxes = driver.find_elements(By.XPATH,"//input[@type='checkbox']")
            # チェックボックスがなかったらwarn吐いてスキップ
            if len(checkboxes) == 0:
                log.warning('.. no checkboxes! check the source')
                can_btn.click()
                continue
            for c in checkboxes:
                c.click()
                log.info('checkbox:{}'.format(c.find_element(By.XPATH,'..').text))
            can_btn.click()
        time.sleep(3)
#        can_btn.click()
        is_recorded = True
        break
    return is_recorded


if __name__ == '__main__':
    log = logging.getLogger('wkml3')
    log.setLevel(logging.DEBUG)
#    h = logging.StreamHandler()
    h = logging.handlers.TimedRotatingFileHandler('{}/wkml3.log'.format(LOGDIR), 'D', 2, 45)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    log.addHandler(h)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(h)
    lambda_handler({}, {})
