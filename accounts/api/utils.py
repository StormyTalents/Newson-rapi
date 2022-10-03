from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions
from time import sleep
from django.conf import settings
import smtplib
from base.utils import give_totally_random_number_in_float, chooseRandomly, waitRandomly, get_avatar, load_cookie, save_cookie, start_driver, get_proxy_options, start_kameleo
from accounts.models import LinkedinAccount
from rest_framework_simplejwt.tokens import RefreshToken
import re
from imap_tools import MailBox, A
from datetime import date, timedelta
from django.utils import timezone
import requests
from http.cookies import SimpleCookie


def check_if_proxy_works(proxy):
    proxies = {
        "http": f"http://{proxy['username']}:{proxy['password']}@{proxy['server']}:{proxy['port']}/",
        "https": f"http://{proxy['username']}:{proxy['password']}@{proxy['server']}:{proxy['port']}/",
    }

    url = 'https://api.ipify.org'

    try:
        response = requests.get(url, proxies=proxies)
        print(response.text)
        return True
    except:
        return False


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def test_smtp_server(smtp, port, username, password, smtp_ssl):

    if smtp_ssl:
        server = smtplib.SMTP_SSL(smtp, port, timeout=20)
    else:
        server = smtplib.SMTP(smtp, port, timeout=20)

    server.set_debuglevel(1)
    server.login(username, password)
    server.quit()


def connect_your_linkedin_with_verification_code(request, verification_code, linkedin_account):

    driver, success = start_driver(action="connect_your_linkedin_with_verification_code", proxy = linkedin_account.get_proxy)
        
    connected = True
    msg = ""
    driver.get("https://www.linkedin.com/")

    try:
        cookie_accept_elem = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[action-type="ACCEPT"]')))
        sleep(1)
        cookie_accept_elem.click()
    except exceptions.TimeoutException:
        pass

    load_cookie(driver, f"linkedin-account-{linkedin_account.username}-{request.user.userprofile.id}")

    driver.get(linkedin_account.verification_code_url)

    # driver.save_screenshot(f"{linkedin_account.id}-{linkedin_account.username}.png")
    
    # sleep(1000)

    code = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'input[type="number"]')))

    submit_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'form button[type="submit"]')))

    code.send_keys(f"{verification_code}")

    sleep(2)

    old_url = driver.current_url

    submit_btn.click()
    
    sleep(1)
    
    try:
        error = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="alert"]'))).text
    except exceptions.TimeoutException as e:
        error = ""

    if driver.current_url == old_url and error:
        connected = False
        msg = f"{error}"

    elif "feed" in driver.current_url:
        profile_image = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module__actor-meta>a>div>img")))
        profile_name = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module__actor-meta>a>div:nth-child(2)")))
        profile_link = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module__actor-meta>a")))
        avatar = get_avatar(profile_image.get_attribute("src"))
        
        header_csrf_token = ""
        header_cookie = ""
        
        for drequest in driver.requests:
            
            if 'realtime/connect' in drequest.url:
                header_csrf_token = drequest.headers["csrf-token"]
                header_cookie = drequest.headers["cookie"]

        linkedin_account.name = profile_name.text
        linkedin_account.profile_url = profile_link.get_attribute("href")
        linkedin_account.ready_for_use = True
        linkedin_account.connected = True
        linkedin_account.header_csrf_token = header_csrf_token
        linkedin_account.header_cookie = header_cookie
        linkedin_account.cookies_file_path = save_cookie(driver, f"linkedin-account-{linkedin_account.username}-{request.user.userprofile.id}")
        linkedin_account.save()
        
        profile_id = linkedin_account.linkedin_profile_id
        profile_url_for_profile_urn = f'https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={profile_id}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.TopCardSupplementary-106'
        cookie = SimpleCookie()
        cookie.load(linkedin_account.header_cookie)
        cookies = {k: v.value for k, v in cookie.items()}
        headers = { "Csrf-Token": linkedin_account.header_csrf_token }
        proxies = get_proxy_options(linkedin_account.proxy)["proxy"] if linkedin_account.proxy else {}
        
        ####################################### profile_urn ################################
        resp = requests.get(profile_url_for_profile_urn, cookies=cookies, headers=headers, proxies=proxies)
        profile_urn_json = resp.json()
        profile_urn = profile_urn_json["elements"][0]["entityUrn"]
        linkedin_account.profile_urn = profile_urn
        linkedin_account.save()

        if avatar:
            linkedin_account.avatar.save(f"{linkedin_account.username}-{linkedin_account.id}.jpg", avatar[0])

    else:
        connected = False
        msg = "Please enter correct verification code or check your account!"

    driver.quit()

    return connected, msg


def connect_your_linkedin(request, username, password, timezone, from_hour, to_hour, proxy, linkedin_account=None):
    
    driver, success = start_driver(action="connect_your_linkedin", proxy = proxy)
        
    connected = True
    msg = ""

    driver.get("https://www.linkedin.com/login")

    try:
        cookie_accept_elem = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[action-type="ACCEPT"]')))
        sleep(1)
        cookie_accept_elem.click()
    except exceptions.TimeoutException:
        pass

    username_elem = WebDriverWait(driver, settings.TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#username")))
    password_elem = WebDriverWait(driver, settings.TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#password")))
    login_btn_elem = WebDriverWait(driver, settings.TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".btn__primary--large")))

    username_elem.send_keys(username)
    password_elem.send_keys(password)

    login_btn_elem.click()
    
    sleep(1)

    data = {}
    data["profile"] = request.user.userprofile
    data["username"] = username
    data["password"] = password
    
    print(proxy)
    if proxy.get("id"):
        data["proxy_id"] = proxy.get("id")
    else:
        data["use_custom_proxy"] = True
        data["custom_proxy_username"] = proxy["username"]
        data["custom_proxy_password"] = proxy["password"]
        data["custom_proxy_server"] = proxy["server"]
        data["custom_proxy_port"] = proxy["port"]
        data["custom_proxy_country"] = proxy["country"]
        
    data["timezone"] = timezone
    data["from_hour"] = from_hour
    data["to_hour"] = to_hour

    if "feed" in driver.current_url:
        
        header_csrf_token = ""
        header_cookie = ""
        
        for drequest in driver.requests:
            
            if 'voyager/api/' in drequest.url:
                header_csrf_token = drequest.headers["csrf-token"]
                header_cookie = drequest.headers["cookie"]
        
        profile_image = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module__actor-meta>a>div>img")))
        profile_name = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module__actor-meta>a>div:nth-child(2)")))
        
        try:
            profile_headline = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".identity-headline"))).text
        except exceptions.TimeoutException as e:
            profile_headline = ""
            
        profile_link = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module__actor-meta>a")))
        avatar = get_avatar(profile_image.get_attribute("src"))
        
        data["name"] = profile_name.text
        data["headline"] = profile_headline
        data["profile_url"] = profile_link.get_attribute("href")
        data["ready_for_use"] = True
        data["connected"] = True
        data["header_csrf_token"] = header_csrf_token
        data["header_cookie"] = header_cookie
        data["cookies_file_path"] = save_cookie(driver, f"linkedin-account-{username}-{request.user.userprofile.id}")

        if linkedin_account:
            for attr, value in data.items():
                setattr(linkedin_account, attr, value)
            linkedin_account.save()
        else:
            linkedin_account = LinkedinAccount.objects.create(**data)
        
        profile_id = linkedin_account.linkedin_profile_id
        profile_url_for_profile_urn = f'https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={profile_id}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.TopCardSupplementary-106'
        cookie = SimpleCookie()
        cookie.load(linkedin_account.header_cookie)
        cookies = {k: v.value for k, v in cookie.items()}
        headers = { "Csrf-Token": linkedin_account.header_csrf_token }
        proxies = get_proxy_options(proxy)["proxy"] if proxy else {}
        
        ####################################### profile_urn ################################
        resp = requests.get(profile_url_for_profile_urn, cookies=cookies, headers=headers, proxies=proxies)
        profile_urn_json = resp.json()
        profile_urn = profile_urn_json["elements"][0]["entityUrn"]
        linkedin_account.profile_urn = profile_urn
        linkedin_account.save()
        
        if avatar:
            linkedin_account.avatar.save(f"{username}-{linkedin_account.id}.jpg", avatar[0])


    elif "checkpoint/challenge" in driver.current_url:
        data.pop("name", "")
        data.pop("headline", "")
        data.pop("profile_url", "")
        data.pop("header_csrf_token", "")
        data.pop("header_cookie", "")
                
        data["verification_code_url"] = driver.current_url
        data["ready_for_use"] = False
        data["connected"] = False
        data["cookies_file_path"] = save_cookie(driver, f"linkedin-account-{username}-{request.user.userprofile.id}")

        if linkedin_account:
            for attr, value in data.items():
                setattr(linkedin_account, attr, value)
            linkedin_account.save()
        else:
            linkedin_account = LinkedinAccount.objects.create(**data)

        connected = False
        msg = "Email Verification Code Needed!"

    else:
        connected = False
        msg = "Please check your account credentials or linkedin account!"
        linkedin_account = None

    driver.quit()

    return connected, msg, linkedin_account


def get_verfication_code_from_imap(imap_host, imap_port, email, password):
    verification_codes = []
    
    sleep(give_totally_random_number_in_float(11, 20))
    
    print([imap_host], [imap_port], [email], [password])
    
    date
    
    with MailBox(str(imap_host), int(imap_port)).login(email, password) as mailbox:
        
        for msg in mailbox.fetch(A( date_gte=timezone.now().date() - timedelta(days=1) ), reverse = True):
            if 'PIN' in msg.subject:
                verification_codes.append(re.findall(r'\d{5,7}', msg.text))
                break
    
    return verification_codes[0], False if len(verification_codes) else True


def get_verification_code_from_gmail(username, linkedin_email_password, linkedin_email_recovery_email, proxy):
    driver = start_kameleo(proxy)
    sleep(give_totally_random_number_in_float())
    
    driver.get('https://mail.google.com/mail/u/0/#inbox')
    
    sleep(give_totally_random_number_in_float())

    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.NAME, 'identifier'))).send_keys(f'{username}\n')
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.NAME, 'password'))).send_keys(f'{linkedin_email_password}\n')
    
    sleep(give_totally_random_number_in_float(5, 10))
    
    try:
        recovery_email_option =  WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, "//div[contains(text(),'your recovery email')]")))
        recovery_email_option.click()
        
        sleep(give_totally_random_number_in_float())
        
        recovery_email_input =  WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//input[@type='email']")))
        recovery_email_input.send_keys(linkedin_email_recovery_email)
        
        driver.executeScript('alert = function(){};');
        driver.executeScript('confirm = function(){};');
        
        next_btn =  WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//span[contains(text(),'Next')]")))
        next_btn.click()
        
    except exceptions.TimeoutException as e:
        print(str(e))
        
        
    print("success")
    sleep(give_totally_random_number_in_float(5, 10))

    driver.get('https://mail.google.com/mail/u/0/?tab=wm#inbox')
    
    sleep(give_totally_random_number_in_float(5, 10))

    unread_pin_email = driver.find_element_by_xpath("(//tr[contains(@class,'zE')]//*[contains(text(),'PIN')])[2]")
    unread_pin_email.click()

    verification_code = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//p[contains(text(),'verification')]//following-sibling::*"))).text
    
    driver.quit()
    
    return verification_code


def get_verification_code_from_yahoo(username, linkedin_email_password, proxy):
    driver = start_kameleo(proxy)
    sleep(give_totally_random_number_in_float())
    
    driver.get('https://login.yahoo.com')
    
    sleep(give_totally_random_number_in_float())

    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//input[@id='login-username']"))).send_keys(f'{username}\n')
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//input[@id='login-passwd']"))).send_keys(f'{linkedin_email_password}\n')
    
    sleep(give_totally_random_number_in_float(2, 5))
    
    driver.get('https://mail.yahoo.com/')
    
    sleep(give_totally_random_number_in_float(2, 5))
    
    driver.find_element_by_xpath('//body').send_keys(Keys.ESCAPE)
    driver.find_element_by_xpath('//body').send_keys(Keys.ESCAPE)
    
    driver.execute_script('document.evaluate("(//span[contains(@class,\'u_Z13VSE6\')][contains(text(),\'PIN\')])[1]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
    verification_code = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//p[contains(text(),'verification')]//following-sibling::*"))).text
    
    driver.quit()
        
    return verification_code


def connect_linkedin_account_with_automatic_verification(driver, row, userprofile, proxy):
    
    username = row["Linkedin Email *"]
    password = row["Linkedin Password *"]
    linkedin_email_password = row["Linkedin Email Password *"]
    linkedin_email_recovery_email = row["Linkedin Email Recovery Email *"]
    imap_host = row["IMAP Host"] or f"imap.{username.split('@')[-1]}"
    imap_port = row["IMAP Port"] or 993
   
    reason = ""
    error_message = ""
    failed = False
    
    driver.get('https://www.linkedin.com/login')

    sleep(give_totally_random_number_in_float(5, 10))

    try:
        cookie_accept_elem = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[action-type="ACCEPT"]')))
        sleep(give_totally_random_number_in_float())
        cookie_accept_elem.click()
    except exceptions.TimeoutException:
        pass

    username_elem = WebDriverWait(driver, settings.TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#username")))
    password_elem = WebDriverWait(driver, settings.TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#password")))
    login_btn_elem = WebDriverWait(driver, settings.TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".btn__primary--large")))

    username_elem.send_keys(username)
    password_elem.send_keys(password)

    login_btn_elem.click()
    
    sleep(give_totally_random_number_in_float())
    

    if "checkpoint/challenge" in driver.current_url:
        
        if "@gmail.com" in username.lower():
            
            try:
                verification_code = get_verification_code_from_gmail(username, linkedin_email_password, linkedin_email_recovery_email, proxy)
            except Exception as e:
                print(str(e))
                error_message = f"{e}"
                reason = "Because Retrieving Gmail Verfication Code Failed!"
                failed = True
                
        elif "@yahoo.com" in username.lower():
            
            try:
                verification_code = get_verification_code_from_yahoo(username, linkedin_email_password, proxy)
            except Exception as e:
                print(str(e))
                error_message = f"{e}"
                reason = "Because Retrieving Yahoo Verfication Code Failed!"
                failed = True
                
        else:
            try:
                verification_code, failed = get_verfication_code_from_imap(imap_host, imap_port, username, linkedin_email_password)
            except Exception as e:
                print(str(e))
                error_message = f"{e}"
                failed = True
                
            if failed:
                reason = "Because Fetching Imap Verfication Code Failed!"
                
        
        if not failed:
            code = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="input__email_verification_pin"]')))

            error = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="email-pin-error"]')))

            submit_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="email-pin-submit-button"]')))

            code.send_keys(f"{verification_code}")

            sleep(give_totally_random_number_in_float())

            old_url = driver.current_url

            submit_btn.click()

            sleep(give_totally_random_number_in_float())

            if driver.current_url == old_url and error.text:
                failed = True
                reason = f"Because the verfication code isn't right!"
                error_message = f"{error.text}"

        sleep(give_totally_random_number_in_float())
        
    if "feed" in driver.current_url and not failed:
        profile_image = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module__actor-meta>a>div>img")))
        profile_name = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module__actor-meta>a>div:nth-child(2)")))
        try:
            profile_headline = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".identity-headline"))).text
        except exceptions.TimeoutException as e:
            profile_headline = ""
        profile_link = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module__actor-meta>a")))
        avatar = get_avatar(profile_image.get_attribute("src"))
        
        header_csrf_token = ""
        header_cookie = ""
        
        for drequest in driver.requests:
            
            if 'realtime/connect' in drequest.url:
                header_csrf_token = drequest.headers["csrf-token"]
                header_cookie = drequest.headers["cookie"]

        linkedin_account = LinkedinAccount.objects.create(
            profile = userprofile,
            username = username,
            password = password,
            name = profile_name.text,
            headline = profile_headline,
            profile_url = profile_link.get_attribute("href"),
            ready_for_use = True,
            connected = True,
            header_csrf_token = header_csrf_token,
            header_cookie = header_cookie,
            cookies_file_path = save_cookie(driver, f"linkedin-account-{username}-{userprofile.id}"),
            proxy = proxy,
        )
        
        profile_id = linkedin_account.linkedin_profile_id
        profile_url_for_profile_urn = f'https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={profile_id}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.TopCardSupplementary-106'
        cookie = SimpleCookie()
        cookie.load(linkedin_account.header_cookie)
        cookies = {k: v.value for k, v in cookie.items()}
        headers = { "Csrf-Token": linkedin_account.header_csrf_token }
        proxies = get_proxy_options(proxy)["proxy"] if proxy else {}
        
        ####################################### profile_urn ################################
        resp = requests.get(profile_url_for_profile_urn, cookies=cookies, headers=headers, proxies=proxies)
        print(resp.content)
        profile_urn_json = resp.json()
        profile_urn = profile_urn_json["elements"][0]["entityUrn"]
        linkedin_account.profile_urn = profile_urn
        linkedin_account.save()

        if avatar:
            linkedin_account.avatar.save(f"{username}-{linkedin_account.id}.jpg", avatar[0])
    else:
        linkedin_account = LinkedinAccount.objects.create(
            profile = userprofile,
            username = username,
            password = password,
            verification_code_url = driver.current_url,
            ready_for_use = False,
            connected = False,
            cookies_file_path = save_cookie(driver, f"linkedin-account-{username}-{userprofile.id}"),
            proxy = proxy,
        )
        
        if not failed:
            failed = True
            reason = "Sorry, something went wrong!"


    return failed, reason, error_message