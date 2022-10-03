import os
import pickle
from django.conf import settings
# from selenium import webdriver
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions
import requests
from django.core import files
from io import BytesIO
import seleniumwire.undetected_chromedriver as uc
from random import randint, choice, sample, uniform
from selenium_stealth import stealth
from kameleo.local_api_client.kameleo_local_api_client import KameleoLocalApiClient
from kameleo.local_api_client.builder_for_create_profile import BuilderForCreateProfile
from kameleo.local_api_client.models.server_py3 import Server
from kameleo.local_api_client.models.problem_response_py3 import ProblemResponseException
from selenium import webdriver as sel_webdriver


def give_totally_random_number_in_float(min_=4, max_=7):
    
    if type(min_) == int and min_ > 0:
        min_ = min_-0.1
        
    if type(max_) == int and max_ > 0:
        max_ = max_+0.12
    
    return chooseRandomly(*[uniform(max_, min_) for i in range(100)])


def chooseRandomly(*args):
    return choice(args)


def waitRandomly(*args):
    random_wait = choice(args)
    sleep(uniform(random_wait["from"], random_wait["to"]))


def refresh_google_access_token(refresh_token):

    data = {
        'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    response = requests.post("https://www.googleapis.com/oauth2/v4/token", data=data)

    if not response.ok:
        return False

    access_token = response.json()['access_token']
    id_token = response.json()['id_token']

    return (access_token, id_token)


def get_avatar(url):
    if "data:image" in url or not "http" in url:
        return None

    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        return None

    if response.status_code != requests.codes.ok:
        return None

    fp = BytesIO()
    fp.write(response.content)
    return (files.File(fp), True,)


def get_proxy_options(proxy):
    return {
        "proxy": {}
    }
    # return {
    #     'proxy': {
    #         'http': f"http://{proxy['username']}:{proxy['password']}@{proxy['server']}:{proxy['port']}",
    #         'https':f"http://{proxy['username']}:{proxy['password']}@{proxy['server']}:{proxy['port']}",
    #     } if proxy else {},
    #     'disable_encoding' : True,
    #     'verify_ssl': False, 
    #     # 'ignore_http_methods': ['GET', 'POST', 'OPTIONS']
    # }


def start_kameleo(proxy=None):
    client = KameleoLocalApiClient(settings.KAMELEO_HOST)
    base_profiles = client.search_base_profiles(
        device_type='desktop',
        browser_product='chrome',
        language='en-us'
    )
    create_profile_request = BuilderForCreateProfile \
            .for_base_profile(base_profiles[0].id) \
            .set_recommended_defaults() \
    
    if proxy:
        create_profile_request = create_profile_request.set_proxy('socks5', Server(
            host=proxy.server, port=50101, id=proxy.credential.username,
            secret=proxy.credential.password))
        
    create_profile_request = create_profile_request.build()
    profile = client.create_profile(body=create_profile_request)
    client.start_profile(profile.id)

    options = sel_webdriver.ChromeOptions()
    options.add_experimental_option("kameleo:profileId", profile.id)
    
    driver = sel_webdriver.Remote(
        command_executor=f'{settings.KAMELEO_HOST}/webdriver',
        options=options
    )

    return driver


def start_driver(linkedin_account=None, action_to_do_if_cookie_failed=None, action="Default", proxy = None):
    
    
    if not proxy and not (linkedin_account and linkedin_account.get_proxy):
        return "No Proxy is Supplied", False
    
    if proxy:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=settings.DRIVER_OPTIONS, seleniumwire_options=get_proxy_options(proxy or linkedin_account.get_proxy))
    elif linkedin_account:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=settings.DRIVER_OPTIONS, seleniumwire_options=get_proxy_options(linkedin_account.get_proxy))
    else:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=settings.DRIVER_OPTIONS)
        
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

        
    if not linkedin_account:
        return driver, True
        
    driver.get("https://www.linkedin.com/")

    cookie = load_cookie(driver, f"linkedin-account-{linkedin_account.username}-{linkedin_account.profile.id}")

    print(cookie)

    try:
        cookie_accept_elem = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[action-type="ACCEPT"]')))
        sleep(give_totally_random_number_in_float(0, 2))
        cookie_accept_elem.click()
    except exceptions.TimeoutException:
        pass

    if not cookie:
        driver.quit()
        linkedin_account.connected = False
        linkedin_account.cookies_file_path = ""
        linkedin_account.verification_code_url = ""
        linkedin_account.ready_for_use = False
        linkedin_account.save()

        if action_to_do_if_cookie_failed:
            return action_to_do_if_cookie_failed(linkedin_account), False

        print("Cookie Loading Failed!!!")

        return "Cookie Loading Failed!!!", False

    driver.get(linkedin_account.profile_url)

    sleep(give_totally_random_number_in_float())

    if not f"{linkedin_account.profile_url}" in driver.current_url:
        driver.quit()
        linkedin_account.connected = False
        linkedin_account.cookies_file_path = ""
        linkedin_account.verification_code_url = ""
        linkedin_account.ready_for_use = False
        linkedin_account.save()

        print("User Linkedin Account Expired!!!")

        return "User Linkedin Account Expired!!!", False

    return driver, True


def create_a_dir_if_it_doesnot_exist(path):
    # Check whether the specified path exists or not
    isExist = os.path.exists(path)

    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(path)


def save_cookie(driver, path):

    create_a_dir_if_it_doesnot_exist(settings.COOKIES_ROOT)

    cookie_file_path = os.path.join(settings.COOKIES_ROOT, f"{path}.txt")

    with open(cookie_file_path, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)

    return cookie_file_path


def load_cookie(driver, path):

    cookie_file_path = os.path.join(settings.COOKIES_ROOT, f"{path}.txt")

    if not os.path.exists(cookie_file_path):
        driver.quit()
        return None

    with open(cookie_file_path, 'rb') as cookiesfile:
        cookies = pickle.load(cookiesfile)

        for cookie in cookies:

            if 'sameSite' in cookie:
                if cookie['sameSite'] == 'None':
                    cookie['sameSite'] = 'Strict'

            driver.add_cookie(cookie)

    return True
