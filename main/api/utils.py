from datetime import datetime, timedelta, date
from django.utils import timezone
from django.conf import settings
from django.core import files
from io import BytesIO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions
from main.models import (
    Campaign, Prospect, CampaignFailedReason,
    ProspectActionLog, CampaignSequence, Message,
    Room, EmailWebHook, outreach_step_choices, LinkedinAccount,
    CampaignLinkedinAccount, UserLinkedinConnection, PostSequence,
    EngagementCampaignPost
)
from time import sleep
import requests
from selenium.webdriver.common.keys import Keys
import base64
from email.mime.text import MIMEText
import json
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.utils import timezone
from random import randint, sample
from datetime import datetime
import pytz
from base.utils import give_totally_random_number_in_float, chooseRandomly, waitRandomly, get_proxy_options, refresh_google_access_token
import tkinter as tk
import urllib.parse


def check_if_actions_can_run_for_a_linkedin_account(linkedin_account):
    linkedin_account_timezone = pytz.timezone(linkedin_account.timezone)
    current_time_of_linkedin_account = datetime.now(linkedin_account_timezone)
    print(current_time_of_linkedin_account.time(),
          current_time_of_linkedin_account.time())
    print(linkedin_account.from_hour, linkedin_account.to_hour)
    if (
        current_time_of_linkedin_account.time() >= linkedin_account.from_hour and
        current_time_of_linkedin_account.time() <= linkedin_account.to_hour and
        str(current_time_of_linkedin_account.weekday()
            ) in linkedin_account.working_days
    ):
        return True

    return False


def create_prospect_action_log(prospect, action):
    return ProspectActionLog.objects.create(prospect=prospect, action=action)


def blacklist_check(linkedin_account, prospect):
    words = linkedin_account.blacklist.split(",") if linkedin_account.blacklist else []
    
    for word in words:
        new_word = word.lower()
        
        if new_word in prospect.first_name.lower():
            return
        
        if new_word in prospect.last_name.lower():
            return
        
        if new_word in prospect.name.lower():
            return
        
        if new_word in prospect.headline.lower():
            return
        
        if new_word in prospect.occupation.lower():
            return
        
        if new_word in prospect.current_company.lower():
            return
        
        if new_word in prospect.school_university.lower():
            return
        
        if new_word in prospect.bio.lower():
            return
        
        if new_word in prospect.location.lower():
            return
        
        if new_word in prospect.email.lower():
            return
        
        if new_word in prospect.phone.lower():
            return
        
        if new_word in prospect.linkedin_profile_url.lower():
            return
        
        if new_word in prospect.linkedin_sales_navigator_profile_url.lower():
            return
        
    return True # test passed


def get_action_limits(campaign_linkedin_account, action):
    tomorrow = timezone.now() - timedelta(days=1)
    campaigns_of_linkedin_account = CampaignLinkedinAccount.objects.filter(
        linkedin_account=campaign_linkedin_account.linkedin_account
    ).all().exclude(campaign__status="Finished").exclude(campaign__status="Stopped")  # only running campaigns
    batch_size = 35

    if action == "fully_crawl":
        actions = ProspectActionLog.objects.filter(
            prospect__campaign_linkedin_account=campaign_linkedin_account,
            created_at__gte=tomorrow,
            action=outreach_step_choices[0][0],  # Connection Request
        )

        limit = int(campaign_linkedin_account.linkedin_account.connection_requests_per_day_to /
                    campaigns_of_linkedin_account.count()) + 5

        if actions.count() >= limit:
            return 0
        else:
            need_to_do_more = limit - actions.count()
            return batch_size if need_to_do_more > batch_size else need_to_do_more

    elif action == "connection_request":
        actions = ProspectActionLog.objects.filter(
            prospect__campaign_linkedin_account=campaign_linkedin_account,
            created_at__gte=tomorrow,
            action=outreach_step_choices[0][0],  # Connection Request
        )

        limit = int(randint(campaign_linkedin_account.linkedin_account.connection_requests_per_day_from,
                    campaign_linkedin_account.linkedin_account.connection_requests_per_day_to) / campaigns_of_linkedin_account.count())

        if actions.count() >= limit:
            return 0
        else:
            need_to_do_more = limit - actions.count()
            return batch_size if need_to_do_more > batch_size else need_to_do_more

    elif action == "messages":
        actions = ProspectActionLog.objects.filter(
            prospect__campaign_linkedin_account=campaign_linkedin_account,
            created_at__gte=tomorrow,
            action=outreach_step_choices[1][0],  # Send Message
        )

        limit = int(randint(campaign_linkedin_account.linkedin_account.messages_per_day_from,
                    campaign_linkedin_account.linkedin_account.messages_per_day_to) / campaigns_of_linkedin_account.count())

        if actions.count() >= limit:
            return 0
        else:
            need_to_do_more = limit - actions.count()
            return batch_size if need_to_do_more > batch_size else need_to_do_more

    elif action == "inmails":
        actions = ProspectActionLog.objects.filter(
            prospect__campaign_linkedin_account=campaign_linkedin_account,
            created_at__gte=tomorrow,
            action=outreach_step_choices[2][0],  # Send Inmail
        )

        limit = int(randint(campaign_linkedin_account.linkedin_account.inmails_per_day_from,
                    campaign_linkedin_account.linkedin_account.inmails_per_day_to) / campaigns_of_linkedin_account.count())

        if actions.count() >= limit:
            return 0
        else:
            need_to_do_more = limit - actions.count()
            return batch_size if need_to_do_more > batch_size else need_to_do_more

    elif action == "like_3_posts":
        actions = ProspectActionLog.objects.filter(
            prospect__campaign_linkedin_account=campaign_linkedin_account,
            created_at__gte=tomorrow,
            action=outreach_step_choices[3][0],  # Like 3 Posts
        )

        limit = int(randint(campaign_linkedin_account.linkedin_account.like_3_posts_per_day_from,
                    campaign_linkedin_account.linkedin_account.like_3_posts_per_day_to) / campaigns_of_linkedin_account.count())

        if actions.count() >= limit:
            return 0
        else:
            need_to_do_more = limit - actions.count()
            return batch_size if need_to_do_more > batch_size else need_to_do_more

    elif action == "follows":
        actions = ProspectActionLog.objects.filter(
            prospect__campaign_linkedin_account=campaign_linkedin_account,
            created_at__gte=tomorrow,
            action=outreach_step_choices[4][0],  # Follows
        )

        limit = int(randint(campaign_linkedin_account.linkedin_account.follow_per_day_from,
                    campaign_linkedin_account.linkedin_account.follow_per_day_to) / campaigns_of_linkedin_account.count())

        if actions.count() >= limit:
            return 0
        else:
            need_to_do_more = limit - actions.count()
            return batch_size if need_to_do_more > batch_size else need_to_do_more

    elif action == "endorse_top_5_skills":
        actions = ProspectActionLog.objects.filter(
            prospect__campaign_linkedin_account=campaign_linkedin_account,
            created_at__gte=tomorrow,
            action=outreach_step_choices[5][0],  # Endorse Top 5 Skills
        )

        limit = int(randint(campaign_linkedin_account.linkedin_account.endorse_top_5_skills_per_day_from,
                    campaign_linkedin_account.linkedin_account.endorse_top_5_skills_per_day_to) / campaigns_of_linkedin_account.count())

        if actions.count() >= limit:
            return 0
        else:
            need_to_do_more = limit - actions.count()
            return batch_size if need_to_do_more > batch_size else need_to_do_more

    elif action == "emails":
        actions = ProspectActionLog.objects.filter(
            prospect__campaign_linkedin_account=campaign_linkedin_account,
            created_at__gte=tomorrow,
            action=outreach_step_choices[6][0],  # Send Email
        )

        limit = int(randint(campaign_linkedin_account.linkedin_account.emails_per_day_from,
                    campaign_linkedin_account.linkedin_account.emails_per_day_to) / campaigns_of_linkedin_account.count())

        if actions.count() >= limit:
            return 0
        else:
            need_to_do_more = limit - actions.count()
            return batch_size if need_to_do_more > batch_size else need_to_do_more


def get_prospect_details(driver):

    try:
        full_name = driver.find_element_by_css_selector(
            '.text-heading-xlarge').text
    except exceptions.NoSuchElementException as e:
        print("No Full Name Found.")
        full_name = ""

    first_name = ""
    last_name = ""
    names = full_name.split(" ")

    if len(names) >= 2:
        first_name = names[0]
        last_name = names[-1]

    try:
        bio = driver.find_element_by_css_selector(
            '.inline-show-more-text span[aria-hidden="true"]').text
    except exceptions.NoSuchElementException as e:
        print("No Bio Found.")
        bio = ""

    try:
        headline = driver.find_element_by_css_selector(
            "div>div>div.text-body-medium").text

        if " at " in headline:
            data = headline.split(" at ")
            occupation = data[0].strip()
            current_company = data[1].strip()
        else:
            headline = ""

    except exceptions.NoSuchElementException as e:
        headline = ""

    if not headline:

        try:
            occupation = driver.find_element_by_css_selector(
                '.pvs-entity .t-bold span[aria-hidden="true"]').text

            if "posted lately" in occupation:
                occupation = driver.find_elements_by_css_selector(
                    '.pvs-entity .t-bold span[aria-hidden="true"]')

                if len(occupation) > 1:
                    occupation = occupation[1].text
                else:
                    occupation = ""

        except exceptions.NoSuchElementException as e:
            print("No Occupation Found.")
            occupation = ""

        try:
            current_company = driver.find_element_by_css_selector(
                'div[aria-label="Current company"]').text
        except exceptions.NoSuchElementException as e:
            try:
                current_company = driver.find_element_by_css_selector(
                    '.pvs-entity .t-normal span[aria-hidden="true"]').text
            except exceptions.NoSuchElementException as e:
                current_company = ""

            if current_company and not "yrs" in current_company and not "mos" in current_company:

                temp_company = current_company.split("·")[0].strip()

                if "." in temp_company[-1]:
                    temp_company = temp_company[:-1]

                current_company = temp_company
            else:
                current_company = ""
                print("No current_company Found.")

    try:
        school_university = driver.find_element_by_css_selector(
            'div[aria-label="Education"]').text
    except exceptions.NoSuchElementException as e:
        print("No school_university Found.")
        school_university = ""

    return (first_name, last_name, bio, occupation, current_company, school_university)


def add_linkedin_account_info_in_text(text, linkedin_account):

    new_text = text

    attributes = [
        {
            "username": "[[username]]",
        },
        {
            "name": "[[name]]",
        },
        {
            "headline": "[[headline]]",
        },
        {
            "profile_url": "[[profile_url]]",
        },
    ]

    for attribute in attributes:

        for key, value in attribute.items():
            new_text = new_text.replace(value, getattr(
                linkedin_account, key) if getattr(linkedin_account, key) else "")

    return new_text


def add_prospect_info_in_text(text, prospect):

    new_text = text

    attributes = [
        {
            "first_name": "{{first_name}}",
        },
        {
            "last_name": "{{last_name}}",
        },
        {
            "name": "{{full_name}}",
        },
        {
            "headline": "{{headline}}",
        },
        {
            "occupation": "{{occupation}}",
        },
        {
            "current_company": "{{company_name}}",
        },
        {
            "school_university": "{{college_name}}",
        },
        {
            "bio": "{{bio}}",
        },
        {
            "location": "{{location}}",
        },
        {
            "email": "{{email}}",
        },
    ]

    for attribute in attributes:

        for key, value in attribute.items():
            new_text = new_text.replace(value, getattr(
                prospect, key) if getattr(prospect, key) else "")

    return new_text


def get_element_with_possibilities(driver, first_wait, default_wait, *args):
    for arg in args:

        try:
            if not arg.get("method", None):
                filter_query = (By.CSS_SELECTOR, f"{arg['key']}")

            elif arg["method"] == "xpath":
                filter_query = (By.XPATH, f"{arg['key']}")

            element = WebDriverWait(driver, first_wait if arg == args[0] else default_wait).until(
                EC.presence_of_element_located(filter_query))
            return element
        except exceptions.TimeoutException:
            pass

    raise exceptions.NoSuchElementException


def get_elements_with_possibilities(driver, first_wait, default_wait, *args):
    for arg in args:

        try:
            if not arg.get("method", None):
                filter_query = (By.CSS_SELECTOR, f"{arg['key']}")

            elif arg["method"] == "xpath":
                filter_query = (By.XPATH, f"{arg['key']}")

            element = WebDriverWait(driver, first_wait if arg == args[0] else default_wait).until(
                EC.presence_of_all_elements_located(filter_query))

            return element
        except exceptions.TimeoutException:
            pass

    raise exceptions.NoSuchElementException


def scroll(driver, css_selector):
    try:
        scroll_bar_exists = driver.find_element_by_css_selector(css_selector)
    except exceptions.NoSuchElementException:
        scroll_bar_exists = False

    if scroll_bar_exists:

        scroll_points = [round(x * 0.1, 1)
                         for x in range(10, 1000)]  # from 1.0 to 99.9

        for scroll_times in range(2):

            driver.execute_script(
                f'document.querySelector("{css_selector}").scrollTop = document.querySelector("{css_selector}").scrollHeight/0')  # start

            for i in scroll_points:
                driver.execute_script(
                    f'document.querySelector("{css_selector}").scrollTop = document.querySelector("{css_selector}").scrollHeight/{i}')

            driver.execute_script(
                f'document.querySelector("{css_selector}").scrollTop = document.querySelector("{css_selector}").scrollHeight/1')  # end


def send_connection_request_after_the_connection_btn_is_clicked(driver, campaign_sequence, prospect):
    sleep(give_totally_random_number_in_float())

    # how_do_you_know_check
    try:
        work_related_event = driver.find_element_by_css_selector(
            'button[aria-label="Met at a work-related event"]')
        work_related_event.click()

        sleep(give_totally_random_number_in_float())
        how_do_you_know_connect_btn = driver.find_element_by_css_selector(
            "body>div>div>div>div>button")
        how_do_you_know_connect_btn.click()

        sleep(give_totally_random_number_in_float())
    except exceptions.NoSuchElementException as e:
        pass

    if campaign_sequence.note:

        note_btn = driver.find_element_by_css_selector(
            "body>div>div>div>div>button")
        note_btn.click()

        sleep(give_totally_random_number_in_float())

        message_textarea = driver.find_element_by_css_selector(
            "div>textarea")
        message_textarea.send_keys(add_prospect_info_in_text(
            campaign_sequence.note, prospect))

        sleep(give_totally_random_number_in_float())

    send_btn = driver.find_element_by_css_selector(
        "body>div>div>div>div>button:nth-child(2)")

    if not "artdeco-button--disabled" in send_btn.get_attribute("class"):
        send_btn.click()

        sleep(give_totally_random_number_in_float(2, 5))

        prospect.connection_request_sent = True
        prospect.state_status = "Finished"
    else:
        print("no connect btn found")
        prospect.state_status = "Failed"

    return prospect


def get_sales_nav_profile_more_button(driver):

    try:
        svg = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#profile-card-section button[aria-expanded=false][type="button"] span svg')))
        span = svg.find_element_by_xpath("..")
        option_btn = span.find_element_by_xpath("..")
    except (exceptions.NoSuchElementException, exceptions.TimeoutException) as e:
        print("trying second approach for option button")
        option_btn = get_elements_with_possibilities(driver, 5, 5, {
            "key": "button[data-test-overflow-menu]"
        }, {
            "key": ".right-actions-overflow-menu-trigger"
        }, {
            "key": ".artdeco-dropdown__trigger--placement-bottom"
        })

        option_btn = option_btn[-1]

    return option_btn


def get_conversation_of_a_user_from_linkedin_messaging(driver, message_link, linkedin_account):
    conversations = []
    driver.get(message_link)

    print(message_link)

    sleep(give_totally_random_number_in_float(2, 5))

    for i in range(500):
        driver.execute_script(
            'document.querySelector(".msg-s-message-list-content").scrollIntoView()')
        # sleep(give_totally_random_number_in_float())

    sleep(give_totally_random_number_in_float(5, 10))

    try:
        prospect_profile_link = driver.find_element_by_css_selector(
            f".msg-thread__link-to-profile")
    except exceptions.NoSuchElementException as e:
        print("prospect_profile_link not found...")
        return

    prospects = Prospect.objects.filter(campaign_linkedin_account__linkedin_account=linkedin_account,
                                        linkedin_profile_url=prospect_profile_link.get_attribute("href")).all()

    if not prospects:
        print("No Prospects...")
        return

    prospect_profile_name = driver.find_element_by_css_selector(
        f".msg-entity-lockup__entity-title")
    messages = driver.find_elements_by_css_selector(
        ".msg-s-message-list__event")

    for message_element in messages:
        message_details = {}

        try:
            sender_name = message_element.find_element_by_css_selector(
                ".msg-s-message-group__name")
            msgtime = message_element.find_element_by_css_selector(
                ".msg-s-message-group__timestamp")
        except exceptions.NoSuchElementException as e:
            print("user_previous sender_name & msg_time")

        try:
            driver.execute_script(
                "return arguments[0].scrollIntoView(true);", sender_name)
            driver.execute_script(
                "return arguments[0].scrollIntoView(true);", msgtime)
        except:
            print("no scroll")
            continue

        try:
            message = message_element.find_element_by_css_selector(
                ".msg-s-event-listitem__body")
        except exceptions.NoSuchElementException as e:
            print("no message body")
            continue

        if sender_name.text == prospect_profile_name.text:
            # To idenitfy which is prospect and which is "You"
            message_details["message_from"] = "Prospect"
        else:
            message_details["message_from"] = "User"

        message_details["sender"] = sender_name.text
        message_details["prospect_url"] = prospect_profile_link.get_attribute(
            "href")
        message_details["time"] = msgtime.text
        message_details["message"] = message.text
        message_details["platform"] = "Linkedin"

        conversations.append(message_details)

    for prospect in prospects:
        room, created = Room.objects.get_or_create(
            linkedin_account=linkedin_account,
            message_thread=message_link,
            platform="Linkedin"
        )
        room.prospect = prospect
        room.messages.all().delete()
        room.save()

        for message in conversations:
            Message.objects.create(
                room=room,
                message_from=message["message_from"],
                time=message["time"],
                message=message["message"],
            )


def get_conversation_of_a_user_from_linkedin_sales_messaging(driver, message_link, linkedin_account):
    conversations = []
    driver.get(message_link)
    sleep(give_totally_random_number_in_float(5, 10))

    print(message_link)

    for i in range(500):
        driver.execute_script(
            'document.querySelector(".thread-container>section>div>div").scrollIntoView()')
        # sleep(give_totally_random_number_in_float())

    sleep(give_totally_random_number_in_float(5, 10))

    try:
        prospect_profile_link = driver.find_element_by_css_selector(
            f".conversation-insights__section>.link-without-visited-and-hover-state")
    except exceptions.NoSuchElementException as e:
        print("prospect_profile_link not found...")
        return

    prospect_profile_link_id = prospect_profile_link.get_attribute(
        "href").split("people/")[-1].split(",")[0]
    print(prospect_profile_link_id)

    prospects = Prospect.objects.filter(campaign_linkedin_account__linkedin_account=linkedin_account,
                                        linkedin_sales_navigator_profile_url__icontains=prospect_profile_link_id).all()

    if not prospects:
        print("No Prospects...")
        return

    messages_raw = driver.find_elements_by_css_selector(
        "li>article")

    messages = []

    for message in messages_raw:
        messages.append(message.find_element_by_xpath(".."))

    for message_element in messages:
        message_details = {}

        try:
            sender_name = message_element.find_element_by_css_selector(
                "address>span")
            msgtime = message_element.find_element_by_css_selector(
                "article>div>div>time")
        except exceptions.NoSuchElementException as e:
            print("user_previous sender_name & msg_time")

        try:
            driver.execute_script(
                "return arguments[0].scrollIntoView(true);", sender_name)
            driver.execute_script(
                "return arguments[0].scrollIntoView(true);", msgtime)
        except:
            print("no scroll")
            continue

        message = WebDriverWait(message_element, settings.TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".message-content")))

        if not "you" in sender_name.text.lower():
            # To idenitfy which is prospect and which is "You"
            message_details["message_from"] = "Prospect"
        else:
            message_details["message_from"] = "User"

        message_details["sender"] = sender_name.text
        message_details["prospect_url"] = prospect_profile_link.get_attribute(
            "href")
        message_details["time"] = msgtime.text
        message_details["message"] = message.text
        message_details["platform"] = "Linkedin Sales"

        conversations.append(message_details)

    for prospect in prospects:

        room, created = Room.objects.get_or_create(
            linkedin_account=linkedin_account,
            message_thread=message_link,
            platform="Linkedin Sales"
        )
        room.prospect = prospect
        room.messages.all().delete()
        room.save()

        for message in conversations:
            Message.objects.create(
                room=room,
                message_from=message["message_from"],
                time=message["time"],
                message=message["message"],
            )


def check_reply_and_get_conversations_for_linkedin_messaging(driver, linkedin_account):
    ''' This Function needs to run every 1 hour to identify who has replied and it has a dependency of datetime '''

    # Open Linkedin Home Page
    driver.get("https://www.linkedin.com/messaging/")

    sleep(give_totally_random_number_in_float(2, 5))

    scroll(driver, ".msg-conversations-container__conversations-list")

    msg_users = driver.find_elements_by_css_selector(
        ".msg-conversation-listitem__link")

    message_users = []

    for msg_user in msg_users:

        message_time = msg_user.find_element_by_css_selector(
            ".msg-conversation-listitem__time-stamp").text
        message_link = msg_user.get_attribute("href")

        if not "am" in message_time.lower() and not "pm" in message_time.lower():
            continue

        message_time_date_time = datetime.strptime(
            message_time, '%H:%M %p').time()
        now = datetime.strptime(datetime.now().strftime(
            "%I:%M %p"), '%H:%M %p').time()

        dif = datetime.combine(
            date.today(), now) - datetime.combine(date.today(), message_time_date_time)
        difference_in_hours = dif.seconds/3600
        difference_in_hours = 1

        if difference_in_hours > 4:
            print("You're old message...")
            continue

        message_users.append({
            "message_time": message_time,
            "message_link": message_link,
        })

    for msg_user in message_users:
        get_conversation_of_a_user_from_linkedin_messaging(
            driver, msg_user["message_link"], linkedin_account)
        # break

    return "Success"


def check_reply_and_get_conversations_for_linkedin_sales_messaging(driver, linkedin_account):
    ''' This Function needs to run every 1 hour to identify who has replied and it has a dependency of datetime '''

    # Open Linkedin Home Page
    driver.get("https://www.linkedin.com/sales/inbox/")

    sleep(give_totally_random_number_in_float(5, 10))

    try:
        select_sales_navigator_btn = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".action-select-contract")))
        select_sales_navigator_btn.click()
        sleep(give_totally_random_number_in_float(7, 10))
    except (exceptions.NoSuchElementException, exceptions.TimeoutException):
        print("no contact chooser screen")
        pass
    
    if "premium/products" in driver.current_url:
        print("no sales navigator")
        return

    scroll(driver, "section>.overflow-y-auto")

    msg_users = WebDriverWait(driver, 2*60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".conversation-list-item__link")))

    message_users = []

    for msg_user in msg_users:
        message_time = msg_user.find_element_by_css_selector(
            ".conversation-list-item__timestamp").text
        message_link = msg_user.get_attribute("href")

        if not "am" in message_time.lower() and not "pm" in message_time.lower():
            continue

        message_time_date_time = datetime.strptime(
            message_time, '%H:%M %p').time()
        now = datetime.strptime(datetime.now().strftime(
            "%I:%M %p"), '%H:%M %p').time()

        dif = datetime.combine(
            date.today(), now) - datetime.combine(date.today(), message_time_date_time)
        difference_in_hours = dif.seconds/3600

        print(difference_in_hours)

        if difference_in_hours > 4:
            print("You're old message...")
            continue

        message_users.append({
            "message_time": message_time,
            "message_link": message_link,
        })

    for msg_user in message_users:
        get_conversation_of_a_user_from_linkedin_sales_messaging(
            driver, msg_user["message_link"], linkedin_account)

    return "Success"


def send_message_in_linkedin_messaging(driver, message):
    driver.get(message.room.message_thread)

    # start sending message
    input_area = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".msg-form__contenteditable")))

    sleep(give_totally_random_number_in_float())

    input_area.send_keys(message.message)

    sleep(give_totally_random_number_in_float())

    btn = get_button_by_tag_name(driver, "button", "Send")
    btn.click()

    sleep(give_totally_random_number_in_float())

    get_conversation_of_a_user_from_linkedin_messaging(
        driver, message.room.message_thread, message.room.linkedin_account)

    return "Success"


def send_message_in_linkedin_sales_messaging(driver, message):
    driver.get(message.room.message_thread)

    sleep(give_totally_random_number_in_float())

    try:
        select_sales_navigator_btn = driver.find_element_by_css_selector(
            ".action-select-contract")
        select_sales_navigator_btn.click()
        sleep(give_totally_random_number_in_float(7, 10))
    except exceptions.NoSuchElementException:
        print("no contact chooser screen")
        pass

    try:
        subject = WebDriverWait(driver, 15).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".compose-form__subject-field")))
        sleep(give_totally_random_number_in_float())
        subject.send_keys("Response")
    except exceptions.TimeoutException as e:
        print("No Subject Found....")

    # start sending message
    input_area = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".compose-form__message-field")))

    sleep(give_totally_random_number_in_float())

    input_area.send_keys(message.message)

    sleep(give_totally_random_number_in_float())

    btn = get_button_by_tag_name(driver, "button", "Send")
    btn.click()

    sleep(give_totally_random_number_in_float())

    get_conversation_of_a_user_from_linkedin_sales_messaging(
        driver, message.room.message_thread, message.room.linkedin_account)

    return "Success"


def action_to_do_if_cookie_failed_for_campaign(campaign):
    campaign.status = "Failed"
    CampaignFailedReason.objects.create(
        reason="User LinkedIn Account Isn't Properly Connected Because There Is No Cookie File!", campaign=campaign)
    campaign.save()

    return "User LinkedIn Account Isn't Properly Connected Because There Is No Cookie File!"


def get_avatar(url, prospect):
    if "data:image" in url or not "http" in url:
        return None

    response = requests.get(url)

    if response.status_code != requests.codes.ok:
        return None

    fp = BytesIO()
    fp.write(response.content)
    prospect.linkedin_avatar.save(f"{prospect.id}.jpg", files.File(fp))


def get_email(email, prospect):

    if email:
        prospect.email = email
    elif prospect.linkedin_profile_url:
        email_webhook = EmailWebHook.objects.create(prospect=prospect)

        api_endpoint = 'https://nubela.co/proxycurl/api/linkedin/profile/email'
        header_dic = {'Authorization': f'Bearer {settings.PROXY_CURL_API_KEY}'}
        params = {
            'linkedin_profile_url': prospect.linkedin_profile_url,
            'cache': 'no-cache',
            'callback_url': f'{settings.APP_SUMO_BACKEND_HOST}api/email-webhook/{email_webhook.id}/',
        }

        print(api_endpoint)
        print(header_dic)
        print(params)

        response = requests.get(api_endpoint,
                                params=params,
                                headers=header_dic)

        if response.status_code == 200:

            if response.json()["status"] == "email_found":
                prospect.email = response.json()["email"]
            else:
                email_webhook.delete()


def check_salesnavigator(driver):
    try:
        get_element_with_possibilities(driver, 7, 3, {
            "key": '.global-nav__primary-item .app-aware-link[target="_blank"]'
        })
    except Exception as e:
        print(str(e))
        return False

    return True


def generate_url(campaign, page=1):
    return f"{campaign.search_url}&page={page}"


def auto_accept_connection_requests(driver, linkedin_account):
    driver.get(
        "https://www.linkedin.com/mynetwork/invitation-manager/?invitationType=CONNECTION")

    sleep(give_totally_random_number_in_float())

    for i in range(200):
        driver.find_element_by_xpath('//body').send_keys(Keys.HOME)
        driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_DOWN)
        driver.find_element_by_xpath('//body').send_keys(Keys.END)
        driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_UP)
        driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_UP)
        driver.find_element_by_xpath('//body').send_keys(Keys.END)
        sleep(give_totally_random_number_in_float(0, 2))

    prospects_container = driver.find_elements_by_css_selector(
        ".invitation-card__container")

    for container in prospects_container:

        prospect = container.find_element_by_css_selector(
            ".invitation-card__link")
        accept_btn = container.find_element_by_css_selector(
            ".invitation-card__action-container button:nth-child(2)")
        sleep(give_totally_random_number_in_float())
        accept_btn.click()

        UserLinkedinConnection.objects.get_or_create(
            linkedin_account=linkedin_account, linkedin_profile_url=prospect.get_attribute("href"))

        prospect_instances = Prospect.objects.filter(
            campaign_linkedin_account__linkedin_account=linkedin_account, linkedin_profile_url=prospect.get_attribute("href")).distinct()

        for instance in prospect_instances:
            instance.connected = True
            instance.save()

        sleep(give_totally_random_number_in_float(13, 21.2))


def send_connection_requests(campaign_sequence, campaign_linkedin_account, cookies, headers, proxies):
    prospect_filters = {
        "campaign_linkedin_account": campaign_linkedin_account,
        "fully_crawled": True,
        "connection_request_sent": False,
        "connected": False,
        "linkedin_profile_url__isnull": False,
    }

    if campaign_sequence.order:
        prospect_filters["state__order"] = campaign_sequence.order - 1
    else:
        prospect_filters["state__isnull"] = True
        prospect_filters["state_action_finish_time__isnull"] = True

    prospects = Prospect.objects.filter(**prospect_filters).exclude(
        linkedin_profile_url__exact="", state_status="Performing")

    if campaign_sequence.order:
        prospects = prospects.exclude(state_action_finish_time__isnull=True)

    prospects = prospects.distinct(
    )[:get_action_limits(campaign_linkedin_account, "connection_request")]

    for prospect in prospects:

        if prospect.state_action_finish_time:
            dif = (timezone.now() -
                   prospect.state_action_finish_time).total_seconds() / 3600

            if not dif >= campaign_sequence.delay_in_hours + (campaign_sequence.delay_in_days*24):
                print(f"not perform because of duration {dif}")
                continue

        send_connection_request(prospect, campaign_sequence, cookies, headers, proxies)

        sleep(give_totally_random_number_in_float(60, 120))


def send_messages(driver, campaign_sequence, campaign_linkedin_account):
    prospect_filters = {
        "campaign_linkedin_account": campaign_linkedin_account,
        "fully_crawled": True,
        "linkedin_profile_url__isnull": False,
    }
    if campaign_sequence.order:
        prospect_filters["state__order"] = campaign_sequence.order - 1
    else:
        prospect_filters["state__isnull"] = True
        prospect_filters["state_action_finish_time__isnull"] = True

    prospects = Prospect.objects.filter(**prospect_filters).exclude(
        linkedin_profile_url__exact="")

    if campaign_sequence.order:
        prospects = prospects.exclude(state_action_finish_time__isnull=True)

    prospects = prospects.distinct()
    new_prospects = []
    
    for prospect in prospects:
        
        if prospect.state_action_finish_time:
            dif = (timezone.now() -
                   prospect.state_action_finish_time).total_seconds() / 3600

            if not dif >= campaign_sequence.delay_in_hours + (campaign_sequence.delay_in_days*24):
                print(f"not perform because of duration {dif}")
                continue
            
        if campaign_sequence.wait_for_connection_request_to_be_approved and not prospect.connected:
            continue
        
        new_prospects.append(prospect)
            

    for prospect in new_prospects[:get_action_limits(campaign_linkedin_account, "messages")]:

        driver.get(prospect.linkedin_profile_url)

        sleep(give_totally_random_number_in_float())

        send_message(driver, prospect, campaign_sequence)

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("alert accepted")
        except exceptions.TimeoutException:
            print("no alert")

        sleep(give_totally_random_number_in_float(60, 120))


def send_inmails(driver, campaign_sequence, campaign_linkedin_account):
    prospect_filters = {
        "campaign_linkedin_account": campaign_linkedin_account,
        "fully_crawled": True,
        "linkedin_profile_url__isnull": False,
    }
    if campaign_sequence.order:
        prospect_filters["state__order"] = campaign_sequence.order - 1
    else:
        prospect_filters["state__isnull"] = True
        prospect_filters["state_action_finish_time__isnull"] = True

    prospects = Prospect.objects.filter(**prospect_filters).exclude(
        linkedin_profile_url__exact="")

    if campaign_sequence.order:
        prospects = prospects.exclude(state_action_finish_time__isnull=True)

    prospects = prospects.distinct(
    )[:get_action_limits(campaign_linkedin_account, "inmails")]

    for prospect in prospects:

        if prospect.state_action_finish_time:
            dif = (timezone.now() -
                   prospect.state_action_finish_time).total_seconds() / 3600

            if not dif >= campaign_sequence.delay_in_hours + (campaign_sequence.delay_in_days*24):
                print(f"not perform because of duration {dif}")
                continue

        user_account_is_salesnavigator = False if not prospect.linkedin_sales_navigator_profile_url else True

        driver.get(prospect.linkedin_profile_url if not prospect.linkedin_sales_navigator_profile_url else prospect.linkedin_sales_navigator_profile_url)

        sleep(give_totally_random_number_in_float(5, 8))

        if user_account_is_salesnavigator:
            try:
                select_sales_navigator_btn = driver.find_element_by_css_selector(
                    ".action-select-contract")
                select_sales_navigator_btn.click()
                sleep(give_totally_random_number_in_float(7, 10))
            except exceptions.NoSuchElementException:
                print("no contact chooser screen")
                pass

        send_inmail(driver, prospect, campaign_sequence,
                    user_account_is_salesnavigator)

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("alert accepted")
        except exceptions.TimeoutException:
            print("no alert")

        sleep(give_totally_random_number_in_float(60, 120))


def like_3_posts(driver, campaign_sequence, campaign_linkedin_account):
    prospect_filters = {
        "campaign_linkedin_account": campaign_linkedin_account,
        "fully_crawled": True,
        "linkedin_profile_url__isnull": False,
    }
    if campaign_sequence.order:
        prospect_filters["state__order"] = campaign_sequence.order - 1
    else:
        prospect_filters["state__isnull"] = True
        prospect_filters["state_action_finish_time__isnull"] = True

    prospects = Prospect.objects.filter(**prospect_filters).exclude(
        linkedin_profile_url__exact="")

    if campaign_sequence.order:
        prospects = prospects.exclude(state_action_finish_time__isnull=True)

    prospects = prospects.distinct(
    )[:get_action_limits(campaign_linkedin_account, "like_3_posts")]

    for prospect in prospects:

        if prospect.state_action_finish_time:
            dif = (timezone.now() -
                   prospect.state_action_finish_time).total_seconds() / 3600

            if not dif >= campaign_sequence.delay_in_hours + (campaign_sequence.delay_in_days*24):
                print(f"not perform because of duration {dif}")
                continue

        driver.get(prospect.linkedin_profile_url)

        sleep(give_totally_random_number_in_float())

        like_post(driver, prospect, campaign_sequence)

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("alert accepted")
        except exceptions.TimeoutException:
            print("no alert")

        sleep(give_totally_random_number_in_float(60, 120))


def follows(driver, campaign_sequence, campaign_linkedin_account):
    prospect_filters = {
        "campaign_linkedin_account": campaign_linkedin_account,
        "fully_crawled": True,
        "linkedin_profile_url__isnull": False,
    }
    if campaign_sequence.order:
        prospect_filters["state__order"] = campaign_sequence.order - 1
    else:
        prospect_filters["state__isnull"] = True
        prospect_filters["state_action_finish_time__isnull"] = True

    prospects = Prospect.objects.filter(**prospect_filters).exclude(
        linkedin_profile_url__exact="")

    if campaign_sequence.order:
        prospects = prospects.exclude(state_action_finish_time__isnull=True)

    prospects = prospects.distinct(
    )[:get_action_limits(campaign_linkedin_account, "follows")]

    for prospect in prospects:

        if prospect.state_action_finish_time:
            dif = (timezone.now() -
                   prospect.state_action_finish_time).total_seconds() / 3600

            if not dif >= campaign_sequence.delay_in_hours + (campaign_sequence.delay_in_days*24):
                print(f"not perform because of duration {dif}")
                continue

        driver.get(prospect.linkedin_profile_url)

        sleep(give_totally_random_number_in_float())

        follow(driver, prospect, campaign_sequence)

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("alert accepted")
        except exceptions.TimeoutException:
            print("no alert")

        sleep(give_totally_random_number_in_float(60, 120))


def endorse_top_5_skills(driver, campaign_sequence, campaign_linkedin_account):
    prospect_filters = {
        "campaign_linkedin_account": campaign_linkedin_account,
        "fully_crawled": True,
        "connected": True,
        "linkedin_profile_url__isnull": False,
    }
    if campaign_sequence.order:
        prospect_filters["state__order"] = campaign_sequence.order - 1
    else:
        prospect_filters["state__isnull"] = True
        prospect_filters["state_action_finish_time__isnull"] = True

    prospects = Prospect.objects.filter(**prospect_filters).exclude(
        linkedin_profile_url__exact="")

    if campaign_sequence.order:
        prospects = prospects.exclude(state_action_finish_time__isnull=True)

    prospects = prospects.distinct()
    new_prospects = []
    
    for prospect in prospects:
        
        if prospect.state_action_finish_time:
            dif = (timezone.now() -
                   prospect.state_action_finish_time).total_seconds() / 3600

            if not dif >= campaign_sequence.delay_in_hours + (campaign_sequence.delay_in_days*24):
                print(f"not perform because of duration {dif}")
                continue
            
        if campaign_sequence.wait_for_connection_request_to_be_approved and not prospect.connected:
            continue
        
        new_prospects.append(prospect)
    

    for prospect in new_prospects[:get_action_limits(campaign_linkedin_account, "endorse_top_5_skills")]:

        driver.get(prospect.linkedin_profile_url)

        sleep(give_totally_random_number_in_float())

        endorse_top_5_skill(driver, prospect, campaign_sequence)

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("alert accepted")
        except exceptions.TimeoutException:
            print("no alert")

        sleep(give_totally_random_number_in_float(60, 120))


def send_emails(campaign_sequence, campaign_linkedin_account):

    if campaign_sequence.google_account and campaign_sequence.google_account.connected:
        print("Nothing is Connected!!!")
        return

    prospect_filters = {
        "campaign_linkedin_account": campaign_linkedin_account,
        "fully_crawled": True,
        "email__isnull": False,
    }
    if campaign_sequence.order:
        prospect_filters["state__order"] = campaign_sequence.order - 1
    else:
        prospect_filters["state__isnull"] = True
        prospect_filters["state_action_finish_time__isnull"] = True

    prospects = Prospect.objects.filter(**prospect_filters).exclude(
        email__exact="")

    if campaign_sequence.order:
        prospects = prospects.exclude(state_action_finish_time__isnull=True)

    prospects = prospects.distinct(
    )[:get_action_limits(campaign_linkedin_account, "emails")]

    for prospect in prospects:

        if prospect.state_action_finish_time:
            dif = (timezone.now() -
                   prospect.state_action_finish_time).total_seconds() / 3600

            if not dif >= campaign_sequence.delay_in_hours + (campaign_sequence.delay_in_days*24):
                print(f"not perform because of duration {dif}")
                continue

        prospect.state = campaign_sequence
        prospect.state_status = "Performing"
        prospect.state_action_start_time = timezone.now()
        prospect.save()

        if prospect.email and campaign_sequence.google_account and campaign_sequence.google_account.connected:
            sent = send_email_from_google(add_prospect_info_in_text(campaign_sequence.email_subject, prospect), add_prospect_info_in_text(campaign_sequence.email_message, prospect), prospect.email,
                                          campaign_sequence.google_account.email, campaign_sequence.google_account.access_token, campaign_sequence)

            if not sent:
                prospect.state_status = "Failed"
                prospect.state_action_finish_time = timezone.now()
                prospect.save()
                continue

            elif prospect.email and campaign_sequence.smtp_account and campaign_sequence.smtp_account.connected:

                try:
                    send_mail(campaign_sequence.smtp_account.server, campaign_sequence.smtp_account.port, campaign_sequence.smtp_account.username, campaign_sequence.smtp_account.password,
                              campaign_sequence.smtp_account.ssl, prospect.email, add_prospect_info_in_text(campaign_sequence.email_subject, prospect), add_prospect_info_in_text(campaign_sequence.email_message, prospect), campaign_sequence.from_email)
                    sent = True
                except Exception as e:
                    print(str(e))
                    sent = False

                if not sent:
                    prospect.state_status = "Failed"
                    prospect.state_action_finish_time = timezone.now()
                    prospect.save()
                    continue

        prospect.state = campaign_sequence
        prospect.state_status = "Finished"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()

        sleep(give_totally_random_number_in_float(60, 120))


def send_connection_request(prospect, campaign_sequence, cookies={}, headers={}, proxies={}):

    print("sending connection requests")
    prospect.state = campaign_sequence
    prospect.state_status = "Performing"
    prospect.state_action_start_time = timezone.now()
    prospect.save()

    url = "https://www.linkedin.com/voyager/api/voyagerRelationshipsDashMemberRelationships?action=verifyQuotaAndCreate"
    
    payload = json.dumps({
        "inviteeProfileUrn": f"urn:li:fsd_profile:{prospect.entity_urn}",
        "customMessage": add_prospect_info_in_text(campaign_sequence.note, prospect)
    })
    
    resp = requests.post(url, data=payload, cookies=cookies, headers=headers, proxies=proxies)
    
    if resp.status_code == 200:
        prospect.connection_request_sent = True
        prospect.state_status = "Finished"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()
        
        create_prospect_action_log(prospect, outreach_step_choices[0][0])
        
    else:
        prospect.state_status = "Failed"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()


def send_message(driver, prospect, campaign_sequence):
    continue_ = False

    prospect.state = campaign_sequence
    prospect.state_status = "Performing"
    prospect.state_action_start_time = timezone.now()
    prospect.save()

    try:

        message_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.message-anywhere-button")))[-1]

        message_btn.click()

        sleep(give_totally_random_number_in_float(5, 8))

        message_input = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".msg-form__contenteditable")))[-1]

        message_input.send_keys(add_prospect_info_in_text(
            campaign_sequence.message, prospect))

        sleep(give_totally_random_number_in_float(5, 8))

        message_input.send_keys(Keys.CONTROL + Keys.ENTER)

        sleep(give_totally_random_number_in_float(7, 10))

        message_inputs = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".msg-form__contenteditable")))

        for msg_input in message_inputs:
            msg_input.click()
            msg_input.send_keys(Keys.ESCAPE)
            try:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert.accept()
                print("alert accepted")
            except exceptions.TimeoutException:
                print("no alert")

        prospect.state = campaign_sequence
        prospect.state_status = "Finished"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()
        create_prospect_action_log(
            prospect, outreach_step_choices[1][0])  # Send Message

    except Exception as e:
        print(
            "\n\n", f"Failed Follow Up Message Because Of Unknown Reason:\n{prospect.campaign_linkedin_account.linkedin_account.name}\n{prospect.linkedin_profile_url}", "\n\n")
        print("\n\n", str(e), "\n\n")
        prospect.state = campaign_sequence
        prospect.state_status = "Failed"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()
        continue_ = True

    return continue_


def send_inmail(driver, prospect, campaign_sequence, user_account_is_salesnavigator):

    prospect.state = campaign_sequence
    prospect.state_status = "Performing"
    prospect.state_action_start_time = timezone.now()
    prospect.save()
    tab_list = []

    try:
        if not user_account_is_salesnavigator:
            salesnav_button = get_button_by_tag_name(
                driver, "span", "View in Sales Navigator")

            if not salesnav_button:
                print("View in Sales Navigator Button Not Found!!")
                return

            salesnav_button.click()

            sleep(give_totally_random_number_in_float(5, 8))

            tab_list = driver.window_handles

            driver.switch_to.window(tab_list[-1])

            sleep(give_totally_random_number_in_float(5, 8))

            # bypass multiple sales nav
            try:
                driver.find_element_by_xpath(
                    "//section[@class='page-content-main list']/ul/li[1]//button").click()
            except:
                pass
            sleep(give_totally_random_number_in_float(5, 8))

        try:
            msg_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//div[@class="profile-topcard-actions-container flex-column pt6"]/div[1]/button/span')))
        except exceptions.TimeoutException:
            buttons = driver.find_elements_by_css_selector(
                "#profile-card-section button")
            msg_btn = None

            for button in buttons:
                if "message" in button.text.lower().strip():
                    msg_btn = button
                    break

            if not msg_btn:
                option_btn = get_sales_nav_profile_more_button(driver)
                sleep(give_totally_random_number_in_float())
                option_btn.click()
                sleep(give_totally_random_number_in_float())

                try:
                    msg_btn = driver.find_element_by_css_selector(
                        'li[data-test-overflow-menu-action="message"] > div')
                except exceptions.NoSuchElementException as e:
                    print("No Message Button Found in dropdown")

                    try:
                        msg_btn = driver.find_element_by_css_selector(
                            'button[data-anchor-send-inmail]')
                    except exceptions.NoSuchElementException as e:
                        raise exceptions.NoSuchElementException(
                            "No Message Button Found anywhere")

        msg_btn.click()

        sleep(give_totally_random_number_in_float(2, 5))

        try:
            subject_btn = driver.find_element_by_xpath(
                '//input[@placeholder="Subject (required)"]')
            subject_btn.send_keys(add_prospect_info_in_text(
                campaign_sequence.inmail_subject, prospect))
        except exceptions.NoSuchElementException as e:
            print("\n\n", "Subject Input Not Found As Well!", "\n\n")
            print("\n\n", str(e), "\n\n")

        sleep(give_totally_random_number_in_float())

        try:
            message_btn = driver.find_element_by_xpath(
                '//textarea[@placeholder="Type your message here…"]')
            message_btn.send_keys(add_prospect_info_in_text(
                campaign_sequence.inmail_message, prospect))
        except exceptions.NoSuchElementException as e:
            print("\n\n", "Message Input Not Found As Well!", "\n\n")
            print("\n\n", str(e), "\n\n")
            return True  # continue

        sleep(give_totally_random_number_in_float())

        buttons = driver.find_elements_by_css_selector(
            ".compose-form__container button")
        send_button = None

        for button in buttons:
            if "send" in button.text.lower().strip():
                send_button = button
                break

        if not send_button:
            return True  # continue

        send_button.click()

        sleep(give_totally_random_number_in_float(5, 8))

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("alert accepted")
        except exceptions.TimeoutException:
            print("no alert")

        prospect.state = campaign_sequence
        prospect.state_status = "Finished"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()

        create_prospect_action_log(
            prospect, outreach_step_choices[2][0])  # Send Inmail

        if not user_account_is_salesnavigator:
            driver.close()

        if tab_list:
            driver.switch_to.window(tab_list[0])

    except Exception as e:
        print(
            "\n\n", f"Failed InMail Because Of Unknown Reason:\n{prospect.campaign_linkedin_account.linkedin_account.name}\n{prospect.linkedin_profile_url}", "\n\n")
        print("\n\n", str(e), "\n\n")
        prospect.state = campaign_sequence
        prospect.state_status = "Failed"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()

    return True  # continue


def like_post(driver, prospect, campaign_sequence):

    sleep(give_totally_random_number_in_float())

    prospect.state = campaign_sequence
    prospect.state_status = "Performing"
    prospect.state_action_start_time = timezone.now()
    prospect.save()

    try:
        activity_button = get_button_by_tag_name(
            driver, "a", "See all activity")

        if not activity_button:
            activity_button = get_button_by_tag_name(
                driver, "a", "Show all activity")

            if not activity_button:
                print("No Activity Button Found..")

        if activity_button:

            activity_button.click()
            sleep(give_totally_random_number_in_float(7, 10))

            print("HERE>>>>.....")

            filter_by_post_button = WebDriverWait(driver, settings.TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Posts"]')))
            filter_by_post_button.click()

            sleep(give_totally_random_number_in_float(5, 10))

            try:
                has_posts = driver.find_element_by_css_selector(
                    ".artdeco-empty-state__headline")
                has_posts = False
                print("No Posts Found")
            except exceptions.NoSuchElementException as e:
                has_posts = True

            if has_posts:

                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_UP)
                driver.find_element_by_xpath(
                    '//body').send_keys(Keys.PAGE_DOWN)
                driver.find_element_by_xpath(
                    '//body').send_keys(Keys.PAGE_DOWN)
                driver.find_element_by_xpath(
                    '//body').send_keys(Keys.PAGE_DOWN)
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_UP)
                driver.find_element_by_xpath('//body').send_keys(Keys.HOME)
                driver.find_element_by_xpath('//body').send_keys(Keys.END)
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_UP)
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_UP)
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_UP)
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_UP)
                driver.find_element_by_xpath('//body').send_keys(Keys.HOME)
                driver.find_element_by_xpath(
                    '//body').send_keys(Keys.PAGE_DOWN)
                driver.find_element_by_xpath('//body').send_keys(Keys.HOME)

                like_btns = WebDriverWait(driver, settings.TIMEOUT).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.react-button__trigger')))

                count = 0

                for like_btn in like_btns:

                    if count > 2:
                        break

                    sleep(0.5)
                    driver.execute_script(
                        "return arguments[0].scrollIntoView({block: 'end', inline: 'nearest'});", like_btn)
                    sleep(0.5)

                    like_btn.click()
                    count += 1

                    sleep(give_totally_random_number_in_float(5, 8))

        prospect.state = campaign_sequence
        prospect.state_status = "Finished"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()

        create_prospect_action_log(
            prospect, outreach_step_choices[3][0])  # Like 3 Posts

        sleep(give_totally_random_number_in_float(14, 21))

    except Exception as e:
        print(
            "\n\n", f"Failed to like post Because Of Unknown Reason:\n{prospect.campaign_linkedin_account.linkedin_account.name}\n{prospect.linkedin_profile_url}", "\n\n")
        print("\n\n", str(e), "\n\n")

        prospect.state = campaign_sequence
        prospect.state_status = "Failed"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()
        return True  # continue

    return False  # continue


def follow(driver, prospect, campaign_sequence):

    prospect.state = campaign_sequence
    prospect.state_status = "Performing"
    prospect.state_action_start_time = timezone.now()
    prospect.save()

    try:

        sleep(give_totally_random_number_in_float())

        more_button = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.XPATH, "(//button[contains(@id,'ember')]//span[contains(text(),'More')])[2]")))
        more_button.click()

        sleep(give_totally_random_number_in_float())
        
        try:
            alreadyfollow_button = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "(//span[contains(@class,'t-normal') and contains(text(),'Unfollow')])[2]")))
        except exceptions.TimeoutException as e:        
            try:
                follow_button = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH,
                                                                                                "(//span[contains(@class,'t-normal') and contains(text(),'Follow')])[2]")))
                follow_button.click()
            except exceptions.TimeoutException:
                follow_button = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.XPATH, "(//div[contains(@class,'pvs-profile-actions')]//span[contains(@class,'artdeco-button__text')])[3]")))

                if "follow" in follow_button.text.lowercase().strip():
                    follow_button.click()
                else:
                    raise Exception

        prospect.state = campaign_sequence
        prospect.state_status = "Finished"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()
        create_prospect_action_log(
            prospect, outreach_step_choices[4][0])  # Follow

    except Exception as e:
        print(
            "\n\n", f"Failed Follow Because Of Unknown Reason:\n{prospect.campaign_linkedin_account.linkedin_account.name}\n{prospect.linkedin_profile_url}", "\n\n")
        print("\n\n", str(e), "\n\n")
        prospect.state = campaign_sequence
        prospect.state_status = "Failed"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()


def endorse_top_5_skill(driver, prospect, campaign_sequence):

    prospect.state = campaign_sequence
    prospect.state_status = "Performing"
    prospect.state_action_start_time = timezone.now()
    prospect.save()

    try:

        sleep(give_totally_random_number_in_float())

        show_all_skills = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@id='skills']//parent::*//div[@class='pvs-list__footer-wrapper']//a")))
        show_all_skills.click()

        sleep(give_totally_random_number_in_float(5, 10))

        skills = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located(
            (By.XPATH, "(//div[contains(@class,'pvs-list__item')]//span[contains(@class,'artdeco-button__text')])")))
        count = 0

        for idx, skill in enumerate(skills):

            if count >= 5:
                break
            
            skill = driver.find_element_by_xpath(f"(//div[contains(@class,'pvs-list__item')]//span[contains(@class,'artdeco-button__text')])[{idx + 1}]")
            skill.click()
            sleep(give_totally_random_number_in_float(5, 10))
            count += 1

        prospect.state = campaign_sequence
        prospect.state_status = "Finished"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()
        create_prospect_action_log(
            prospect, outreach_step_choices[5][0])  # Endorse Top 5 Skills

    except Exception as e:
        print(
            "\n\n", f"Failed Endorse Top 5 Skills Because Of Unknown Reason:\n{prospect.campaign_linkedin_account.linkedin_account.name}\n{prospect.linkedin_profile_url}", "\n\n")
        print("\n\n", str(e), "\n\n")
        prospect.state = campaign_sequence
        prospect.state_status = "Failed"
        prospect.state_action_finish_time = timezone.now()
        prospect.save()


def send_mail(smtp, port, username, password, smtp_ssl, to_email, subject, message, from_email):
    backend = EmailBackend(host=smtp, port=port, username=username,
                           password=password, use_ssl=smtp_ssl, fail_silently=False, timeout=60)

    email = EmailMessage(subject=subject, body=message, from_email=from_email, to=[
                         to_email], connection=backend)

    email.send()
    print('successfully sent the mail.')


def send_email_from_google(subject, body, to, from_, access_token, campaign_sequence):
    message = MIMEText(body)
    message['to'] = to
    message['from'] = from_
    message['subject'] = subject

    response = requests.post("https://www.googleapis.com/gmail/v1/users/me/messages/send", headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }, data=json.dumps({'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}))

    if response.status_code == 401:
        print("REFRESHING THE TOKEN")
        response = refresh_google_access_token(
            campaign_sequence.google_account.refresh_token)

        if not response:
            campaign_sequence.google_account.connected = False
            campaign_sequence.google_account.save()
        else:
            campaign_sequence.google_account.access_token = response[0]
            campaign_sequence.google_account.id_token = response[1]
            campaign_sequence.google_account.connected = True
            campaign_sequence.google_account.save()

            response = requests.post("https://www.googleapis.com/gmail/v1/users/me/messages/send", headers={
                "Authorization": f"Bearer {campaign_sequence.google_account.access_token}",
                "Content-Type": "application/json"
            }, data=json.dumps({'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}))

            if response.status_code == 401:
                campaign_sequence.google_account.connected = False
                campaign_sequence.google_account.save()

    if response.ok:
        return True

    return False


def get_all_prospects_and_save_them_in_to_database(driver, campaign_and_linkedin_account, user_account_is_salesnavigator):
    prospects = []

    if user_account_is_salesnavigator:
        propspect_a_tags = get_elements_with_possibilities(driver, 7, 3,
                                                           {
                                                               "key": ".result-lockup__name>a"
                                                           }, {
                                                               "key": ".artdeco-entity-lockup__title>a"
                                                           })

        print(len(propspect_a_tags))

    else:
        propspect_a_tags = WebDriverWait(driver, settings.TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span>span>.app-aware-link")))

    count = 0

    for prospect in propspect_a_tags:

        if not "/in/" in prospect.get_attribute("href") and not "/sales/" in prospect.get_attribute("href"):
            print("HERE", prospect.get_attribute("href"))
            continue

        profile_link = f'{prospect.get_attribute("href").split("?")[0]}/'

        if not user_account_is_salesnavigator:
            name_elem = prospect.find_element_by_css_selector(
                "span>span>.app-aware-link>span>span:nth-child(1)")
        else:
            name_elem = prospect

        name = name_elem.text

        prospect_data = {
            "name": name,
            "campaign_linkedin_account": campaign_and_linkedin_account,
        }

        if user_account_is_salesnavigator:
            prospect_data["linkedin_sales_navigator_profile_url"] = profile_link

        else:
            prospect_data["linkedin_profile_url"] = profile_link

        prospect, created = Prospect.objects.get_or_create(**prospect_data)

        if blacklist_check(campaign_and_linkedin_account.linkedin_account, prospect):
            count += 1
            prospects.append(prospect)
        else:
            prospect.delete()

    return count, prospects


def fill_in_details_of_prospects_and_perform_the_step(driver, campaign_and_linkedin_account, user_account_is_salesnavigator, prospects, cookies={}, headers={}, proxies={}, perform_actions=True):

    campaign_sequences = CampaignSequence.objects.filter(
        campaign=campaign_and_linkedin_account.campaign).order_by("order")

    for prospect in prospects:
        print("\n\n", prospect.linkedin_profile_url, "\n\n",
              prospect.linkedin_sales_navigator_profile_url, "\n\n\n")
        
        profile_id = prospect.profile_id
        profile_url_for_essential_details = f'https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={profile_id}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.WebTopCardCore-8'
        profile_url_for_contact_info = f'https://www.linkedin.com/voyager/api/identity/profiles/{profile_id}/profileContactInfo'
        profile_url_for_school_company_and_profile_urn = f'https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={profile_id}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.TopCardSupplementary-106'
        
        ####################################### essential details ################################
        
        resp = requests.get(profile_url_for_essential_details, cookies=cookies, headers = headers, proxies=proxies)
        essential_details_json = resp.json()
        
        first_name = essential_details_json["elements"][0]["firstName"]
        last_name = essential_details_json["elements"][0]["lastName"]
        
        try:
            headline = essential_details_json["elements"][0]["headline"]
        except KeyError as e:
            headline = ""
            
        try:
            location = essential_details_json["elements"][0]["geoLocation"]["geo"]["defaultLocalizedName"]
        except KeyError as e:
            location = ""
        
        try:
            profile_image_root = essential_details_json["elements"][0]["profilePicture"]["displayImageReference"]["vectorImage"]["rootUrl"]
            profile_image_200 = essential_details_json["elements"][0]["profilePicture"]["displayImageReference"]["vectorImage"]["artifacts"][1]["fileIdentifyingUrlPathSegment"]
            profile_image = f"{profile_image_root}{profile_image_200}"
        except KeyError as e:
            profile_image = ""
        
        
        ####################################### contact info ################################
        
        resp = requests.get(profile_url_for_contact_info, cookies=cookies, headers = headers, proxies=proxies)
        contact_info_json = resp.json()
        
        email = contact_info_json.get("emailAddress", "")
        
        ####################################### school, company, profile_urn ################################
        resp = requests.get(profile_url_for_school_company_and_profile_urn, cookies=cookies, headers=headers, proxies=proxies)
        school_and_company_and_profile_urn_json = resp.json()
        
        school = list(map(lambda elem: elem.get("school", {}).get("name", "") or elem.get("schoolName", ""), school_and_company_and_profile_urn_json["elements"][0]["profileTopEducation"]["elements"])) or [""]
        school = school[0]
        
        company = list(map(lambda elem: elem.get("company", {}).get("name", "") or elem.get("companyName", ""), school_and_company_and_profile_urn_json["elements"][0]["profileTopPosition"]["elements"])) or [""]
        company = company[0]
        
        profile_urn = school_and_company_and_profile_urn_json["elements"][0]["entityUrn"]
        
        
        ####################################### bio, occupation ################################
        profile_url_for_bio_and_occupation = f'https://www.linkedin.com/voyager/api/graphql?includeWebMetadata=true&variables=(profileUrn:{urllib.parse.quote_plus(profile_urn)})&&queryId=voyagerIdentityDashProfileCards.817fd31c31e97c7c17c9cd5d44c6edea'
        resp = requests.get(profile_url_for_bio_and_occupation, cookies=cookies, headers = headers, proxies=proxies)
        bio_and_occupation_json = resp.json()
        
        bio = [elem["topComponents"][1]["components"]["textComponent"]["text"]["text"] for elem in bio_and_occupation_json["data"]["identityDashProfileCardsByInitialCards"]["elements"] if "ABOUT" in elem["entityUrn"] and elem["topComponents"]]
        bio = bio or [""]
        bio = bio[0]

        occupation = [elem["topComponents"][1]["components"]["fixedListComponent"]["components"][0]["components"]["entityComponent"]["title"]["text"] for elem in bio_and_occupation_json["data"]["identityDashProfileCardsByInitialCards"]["elements"] if "EXPERIENCE" in elem["entityUrn"] and elem["topComponents"]]
        occupation = occupation or [""]
        occupation = occupation[0].split(" at ")[0]
        
        prospect.first_name = first_name
        prospect.last_name = last_name
        prospect.name = f"{first_name} {last_name}"
        prospect.bio = bio
        prospect.occupation = occupation
        prospect.current_company = company
        prospect.school_university = school
        prospect.headline = headline
        prospect.location = location
        prospect.fully_crawled = True
        prospect.entity_urn = profile_urn.split("fsd_profile:")[-1]

        if profile_image:
            get_avatar(profile_image, prospect)

        get_email(email, prospect)

        prospect.save()
        
        if not blacklist_check(campaign_and_linkedin_account.linkedin_account, prospect):
            prospect.delete()
            continue
        
        if not perform_actions:
            sleep(give_totally_random_number_in_float(60, 120))
            continue

        try:
            sleep(give_totally_random_number_in_float(20, 35))
            for campaign_sequence in campaign_sequences:

                if (prospect.state_action_finish_time) and not (((timezone.now() - prospect.state_action_finish_time).total_seconds() / 3600) >= campaign_sequence.delay_in_hours + (campaign_sequence.delay_in_days*24)):
                    print(
                        f"Will not perform action because of duration {(timezone.now() - prospect.state_action_finish_time).total_seconds() / 3600}")
                    continue

                if campaign_sequence.step == "send_connection_request":

                    if prospect.state:

                        if prospect.state == campaign_sequence or prospect.state.order >= campaign_sequence.order:
                            print("Will Not Send Connection Request\n\n")
                            continue

                    send_connection_request(prospect, campaign_sequence, cookies, headers, proxies)

                elif campaign_sequence.step == "send_message":
                    if prospect.state:

                        if prospect.state == campaign_sequence or prospect.state.order >= campaign_sequence.order:
                            print("Will Not Send Message\n\n")
                            continue

                    if campaign_sequence.wait_for_connection_request_to_be_approved and not prospect.connected:
                        break

                    driver.get(prospect.linkedin_profile_url)

                    sleep(give_totally_random_number_in_float())

                    send_message(driver, prospect, campaign_sequence)

                elif campaign_sequence.step == "send_inmail":

                    if prospect.state:

                        if prospect.state == campaign_sequence or prospect.state.order >= campaign_sequence.order:
                            print("Will Not Send In Mail\n\n")
                            continue

                    if user_account_is_salesnavigator:
                        driver.get(
                            prospect.linkedin_sales_navigator_profile_url)
                    else:
                        driver.get(prospect.linkedin_profile_url)

                    sleep(give_totally_random_number_in_float())

                    send_inmail(driver, prospect, campaign_sequence,
                                user_account_is_salesnavigator)

                elif campaign_sequence.step == "like_3_posts":

                    if prospect.state:

                        if prospect.state == campaign_sequence or prospect.state.order >= campaign_sequence.order:
                            print("Will Not Like 3 Posts\n\n")
                            continue

                    driver.get(prospect.linkedin_profile_url)

                    sleep(give_totally_random_number_in_float())

                    like_post(driver, prospect, campaign_sequence)

                elif campaign_sequence.step == "follow":

                    if prospect.state:

                        if prospect.state == campaign_sequence or prospect.state.order >= campaign_sequence.order:
                            print("Will Not follow\n\n")
                            continue

                    driver.get(prospect.linkedin_profile_url)

                    sleep(give_totally_random_number_in_float())

                    follow(driver, prospect, campaign_sequence)

                elif campaign_sequence.step == "endorse_top_5_skills":

                    if prospect.state:

                        if prospect.state == campaign_sequence or prospect.state.order >= campaign_sequence.order:
                            print("Will Not Endorese Top 5 Skills\n\n")
                            continue
                        
                    if campaign_sequence.wait_for_connection_request_to_be_approved and not prospect.connected:
                        break

                    driver.get(prospect.linkedin_profile_url)

                    sleep(give_totally_random_number_in_float())

                    endorse_top_5_skill(driver, prospect, campaign_sequence)

                elif campaign_sequence.step == "send_email":

                    if prospect.state:

                        if prospect.state == campaign_sequence or prospect.state.order >= campaign_sequence.order:
                            print("Will Not Send Email\n\n")
                            continue

                    prospect.state = campaign_sequence
                    prospect.state_status = "Performing"
                    prospect.state_action_start_time = timezone.now()
                    prospect.save()

                    if prospect.email and campaign_sequence.google_account and campaign_sequence.google_account.connected:
                        sent = send_email_from_google(add_prospect_info_in_text(campaign_sequence.email_subject, prospect), add_prospect_info_in_text(campaign_sequence.email_message, prospect), prospect.email,
                                                        campaign_sequence.google_account.email, campaign_sequence.google_account.access_token, campaign_sequence)

                        if not sent:
                            prospect.state_status = "Failed"
                            prospect.state_action_finish_time = timezone.now()
                            prospect.save()
                            continue

                    elif prospect.email and campaign_sequence.smtp_account and campaign_sequence.smtp_account.connected:

                        try:
                            send_mail(campaign_sequence.smtp_account.server, campaign_sequence.smtp_account.port, campaign_sequence.smtp_account.username, campaign_sequence.smtp_account.password,
                                        campaign_sequence.smtp_account.ssl, prospect.email, add_prospect_info_in_text(campaign_sequence.email_subject, prospect), add_prospect_info_in_text(campaign_sequence.email_message, prospect), campaign_sequence.from_email)
                            sent = True
                        except Exception as e:
                            print(str(e))
                            sent = False

                        if not sent:
                            prospect.state_status = "Failed"
                            prospect.state_action_finish_time = timezone.now()
                            prospect.save()
                            continue

                    prospect.state_status = "Finished"
                    prospect.state_action_finish_time = timezone.now()
                    prospect.save()
                    continue

                try:
                    WebDriverWait(driver, 3).until(EC.alert_is_present())
                    alert = driver.switch_to.alert
                    alert.accept()
                    print("alert accepted")
                except exceptions.TimeoutException:
                    print("no alert")
        except Exception as e:
            print(str(e), "Campaign Prospect Failed!....",
                  prospect.linkedin_sales_navigator_profile_url, prospect.name)
            continue
        
        sleep(give_totally_random_number_in_float(60, 120))


def post_an_image(driver, sequence):
    image_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-creation-state__detour-btn-container>span:nth-child(1)>button")))
    image_btn.click()
    
    sleep(give_totally_random_number_in_float())
    
    image_input = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#image-sharing-detour-container__file-input")))
    image_input.send_keys(sequence.image.path)
    
    sleep(give_totally_random_number_in_float())
    
    alt_text_tab = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".image-sharing-detour-image-carousel__tablist>button:nth-child(3)")))
    alt_text_tab.click()
    
    sleep(give_totally_random_number_in_float())
    
    alt_text_input = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".image-sharing-detour-alt-text")))
    alt_text_input.send_keys(sequence.image_alt_text)
    
    alt_text_save_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".fr .artdeco-button--primary")))
    alt_text_save_btn.click()
    
    sleep(give_totally_random_number_in_float())
    
    done_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-box-footer__main-actions .ml2")))
    
    done_btn.click()
    
    sleep(give_totally_random_number_in_float())


def post_an_video(driver, sequence):
    video_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-creation-state__detour-btn-container>span:nth-child(2)>button")))
    video_btn.click()
    
    sleep(give_totally_random_number_in_float())
    
    video_input = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#video-detour__file-input")))
    video_input.send_keys(sequence.video.path)
    
    sleep(give_totally_random_number_in_float())
    
    if sequence.video_thumbnail:
        video_thumbnail = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#video-detour-thumbnail-upload-input")))
        video_thumbnail.send_keys(sequence.video_thumbnail.path)
    
        sleep(give_totally_random_number_in_float())
    
    done_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-box-footer__main-actions .ml2")))
    
    done_btn.click()
    
    sleep(give_totally_random_number_in_float())


def post_an_document(driver, sequence):
    document_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-creation-state__detour-btn-container>span:nth-child(3)>button")))
    document_btn.click()
    
    sleep(give_totally_random_number_in_float())
    
    document_input = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".cloud-filepicker-visually-hidden")))
    document_input.send_keys(sequence.document.path)
    
    sleep(give_totally_random_number_in_float())
    
    document_title = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".document-title-form__title-input")))
    document_title.send_keys(sequence.document_title)
    
    sleep(give_totally_random_number_in_float())
    
    done_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-box-footer__main-actions .ml2")))
    
    done_btn.click()
    
    sleep(give_totally_random_number_in_float())
    

def post_an_poll(driver, sequence):
    poll_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-creation-state__detour-btn-container>span:nth-child(6)>button")))
    poll_btn.click()
    
    sleep(give_totally_random_number_in_float())
    
    poll_question_input = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".polls-detour__question-field")))
    poll_question_input.send_keys(sequence.poll_question)
    
    sleep(give_totally_random_number_in_float())
    
    option1 = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#poll-option-1")))
    option1.send_keys(sequence.option_1)
    
    sleep(give_totally_random_number_in_float())
    
    option2 = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#poll-option-2")))
    option2.send_keys(sequence.option_2)
    
    sleep(give_totally_random_number_in_float())
    
    driver.execute_script('document.querySelector(".share-box-modal-content__container .mb3 .artdeco-button--secondary").click()')
    driver.execute_script('document.querySelector(".share-box-modal-content__container .mb3 .artdeco-button--secondary").click()')
    
    if sequence.option_3:
        option3 = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#poll-option-3")))
        option3.send_keys(sequence.option_3)
        
        sleep(give_totally_random_number_in_float())
        
    if sequence.option_4:
        option4 = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#poll-option-4")))
        option4.send_keys(sequence.option_4)
        
        sleep(give_totally_random_number_in_float())
        
    duration_select = Select(driver.find_element_by_css_selector('select[aria-labelledby="polls-duration-label"]'))
    duration_select.select_by_visible_text(sequence.poll_duration)
    
    done_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-box-footer__main-actions .ml2")))
    
    done_btn.click()
    
    sleep(give_totally_random_number_in_float())


def post_an_event(driver, sequence):
    more_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-creation-state__detour-btn-container>span:nth-child(7)>button")))
    more_btn.click()
    
    sleep(give_totally_random_number_in_float(0.7, 1))
    
    event_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li-icon[type="calendar"]')))
    event_btn.click()
    
    sleep(give_totally_random_number_in_float())
    
    cover_input = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#file-upload-input-background_edit")))
    cover_input.send_keys(sequence.event_cover_image.path)
    
    sleep(give_totally_random_number_in_float())
    
    try:
        driver.execute_script('document.querySelector(".image-edit-tool-footer__main-actions > .artdeco-button--primary").click()')
    except Exception as e:
        print(str(e))
        
    sleep(give_totally_random_number_in_float())
    
    if sequence.event_type == "Online":
        online_event_type = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'label[for="ef-event-type__radio--online"]')))
        online_event_type.click()
    else: # in person
        in_person_event_type = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'label[for="ef-event-type__radio--in-person"]')))
        in_person_event_type.click()
    
    if sequence.event_type == "Online":
        event_format_input = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ef-event-type__dropdown-trigger")))
        
        driver.execute_script("return arguments[0].scrollIntoView({block: 'end', inline: 'nearest'});", event_format_input)
        
        event_format_input.click()
        
        if sequence.event_format == "LinkedIn Audio Event":
            event_audio_format_option = WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul li[role="option"]:nth-child(1)')))
            event_audio_format_option.click()
        elif sequence.event_format == "LinkedIn Live":
            event_live_format_option = WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul li[role="option"]:nth-child(2)')))
            event_live_format_option.click()
        else:
            event_external_link_format_option = WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul li[role="option"]:nth-child(3)')))
            event_external_link_format_option.click()
            
        sleep(give_totally_random_number_in_float(1, 2))
    
    event_name_input = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#ef-form__name")))
    
    driver.execute_script("return arguments[0].scrollIntoView({block: 'end', inline: 'nearest'});", event_name_input)
    
    event_name_input.send_keys(sequence.event_name)
    
    sleep(give_totally_random_number_in_float(1, 2))
    
    timezone_select = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#timezone-picker-dropdown-trigger")))
    
    driver.execute_script("return arguments[0].scrollIntoView({block: 'end', inline: 'nearest'});", timezone_select)
    
    timezone_select.click()
    
    sleep(give_totally_random_number_in_float())
    
    timezones = WebDriverWait(driver, 7).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".artdeco-dropdown__content-inner > ul > li > div")))
    
    for timezone in timezones:
        
        if timezone.text in sequence.event_timezone:
            timezone.click()
            break
        
    sleep(give_totally_random_number_in_float(1, 2))
    
    start_date = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='date-time-picker-v2__start-date']")))
    
    start_date.clear()
    start_date.send_keys(f"{sequence.event_start_date_time.date().month}/{sequence.event_start_date_time.date().day}/{sequence.event_start_date_time.date().year}")
    
    sleep(give_totally_random_number_in_float(1, 2))
    
    start_time = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='date-time-picker-v2__start-time']")))
    
    start_time.clear()
    start_time.send_keys(sequence.event_start_date_time.strftime("%I:%M %p"))
    
    sleep(give_totally_random_number_in_float(1, 2))
    
    if not sequence.event_end_date_time and sequence.event_type != "Online":
        add_end_date_time_check_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'label[for="add-end-date-time"]')))
        add_end_date_time_check_btn.click()
    else:
        end_date = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='date-time-picker-v2__start-date']")))
    
        end_date.clear()
        end_date.send_keys(f"{sequence.event_end_date_time.date().month}/{sequence.event_end_date_time.date().day}/{sequence.event_end_date_time.date().year}")
        
        end_time = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@id='date-time-picker-v2__start-time']")))
        
        end_time.clear()
        end_time.send_keys(sequence.event_end_date_time.strftime("%I:%M %p"))
        
        
    if sequence.event_type != "Online":
        sleep(give_totally_random_number_in_float(1, 2))
    
        event_address = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#ef-location-control__input")))
        event_address.send_keys(sequence.event_address)
        
        sleep(give_totally_random_number_in_float(3, 6))
        
        event_address.send_keys(Keys.DOWN)
        event_address.send_keys(Keys.ENTER)
        
        sleep(give_totally_random_number_in_float(1, 2))
        
        if sequence.event_venue:
            event_venue = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#ef-location-fields-venue-details-form-control")))
            event_venue.send_keys(sequence.event_venue)
            
            sleep(give_totally_random_number_in_float(1, 2))
            
        if sequence.event_external_event_link:
            event_external_event_link = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#ef-location-fields-external-url-form-control")))
            event_external_event_link.send_keys(sequence.event_external_event_link)
        
    sleep(give_totally_random_number_in_float(1, 2))
    
    event_description = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".artdeco-text-input__textarea")))
    event_description.send_keys(sequence.event_description)
    
    sleep(give_totally_random_number_in_float())
    
    if sequence.event_speakers:
        search_speaker = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@id='ef-form-control-speaker-typeahead-input']")))
        search_speaker.send_keys(sequence.event_speakers)
        
        sleep(give_totally_random_number_in_float(3, 6))
        
        search_speaker.send_keys(Keys.DOWN)
        search_speaker.send_keys(Keys.ENTER)
        
        sleep(give_totally_random_number_in_float())

    
    done_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-box-footer__main-actions .ml2")))
    
    done_btn.click()
    
    sleep(give_totally_random_number_in_float())
    

def post_an_job(driver, sequence):
    hiring_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-creation-state__detour-btn-container>span:nth-child(4)>button")))
    hiring_btn.click()
    
    sleep(give_totally_random_number_in_float())
    
    job_title_input = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Add the title you are hiring for"]')))
    
    job_title_input.send_keys(sequence.job_title)
    
    sleep(give_totally_random_number_in_float(3, 6))
    
    job_title_input.send_keys(Keys.DOWN)
    job_title_input.send_keys(Keys.ENTER)
    
    sleep(give_totally_random_number_in_float(1, 2))
    
    search_company = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".job-posting-shared-company-typeahead__input")))
    
    for i in range(100):
        search_company.send_keys(Keys.BACK_SPACE)

    
    search_company.send_keys(sequence.job_company)
    
    sleep(give_totally_random_number_in_float(3, 6))
    
    search_company.send_keys(Keys.DOWN)
    search_company.send_keys(Keys.ENTER)
        
    sleep(give_totally_random_number_in_float())
    
    workplace_type_selection = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".job-posting-shared-workplace-type-selection__dropdown-trigger")))
    
    driver.execute_script('document.querySelector("textarea").scrollIntoView({block: \'end\', inline: \'nearest\'});')
    
    sleep(give_totally_random_number_in_float(1, 2))

    workplace_type_selection.click()
    
    sleep(give_totally_random_number_in_float())
    
    print(f'//li//div[text()="{sequence.job_workplace_type}"]')
    
    workplace_type_option = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, f'//li//div[text()="{sequence.job_workplace_type}"]')))
    workplace_type_option.click()
    
    sleep(give_totally_random_number_in_float(1, 2))
    
    job_location_input = WebDriverWait(driver, 7).until(
        EC.presence_of_element_located((By.XPATH, "//input[contains(@id,'location-typeahead-input')]")))

    if sequence.job_location:
        job_location_input.send_keys(sequence.job_location)
    elif sequence.employee_location:
        job_location_input.send_keys(sequence.employee_location)
    
    sleep(give_totally_random_number_in_float(3, 6))
    
    job_location_input.send_keys(Keys.DOWN)
    job_location_input.send_keys(Keys.ENTER)
    
    sleep(give_totally_random_number_in_float(1, 2))
    
    job_type_select = Select(driver.find_element_by_xpath("//select[contains(@id,'employment-type')]"))
    job_type_select.select_by_visible_text(sequence.job_type)
    
    sleep(give_totally_random_number_in_float(1, 2))
    
    job_description = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea")))
    job_description.send_keys(sequence.job_description)
    
    sleep(give_totally_random_number_in_float())
    
    done_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".share-box-footer__main-actions .ml2")))
    
    done_btn.click()
    
    sleep(give_totally_random_number_in_float())


def post_posts_on_linkedin_account(driver, campaign_and_linkedin_account):
    post_sequences = PostSequence.objects.filter(
        campaign=campaign_and_linkedin_account.campaign).order_by("order")

    for sequence in post_sequences:

        post_campaign_post = EngagementCampaignPost.objects.filter(
            campaign_linkedin_account=campaign_and_linkedin_account,
            state=sequence,
        ).first()
        
        post_campaign_post_previous = EngagementCampaignPost.objects.filter(
            campaign_linkedin_account=campaign_and_linkedin_account,
            state__campaign=campaign_and_linkedin_account.campaign,
            state__order=sequence.order - 1,
        ).first()
        
        if (
            post_campaign_post_previous and
            post_campaign_post_previous.state_action_finish_time and
            not ((timezone.now() - post_campaign_post_previous.state_action_finish_time).total_seconds() / 3600) >= sequence.delay_in_hours + (sequence.delay_in_days*24)
        ):
            print(f"Will not post because of duration {(timezone.now() - post_campaign_post_previous.state_action_finish_time).total_seconds() / 3600}")
            continue

        if post_campaign_post and post_campaign_post.state_status != "Failed" and post_campaign_post.post_link: # duplicate check
            continue
        elif not post_campaign_post:
            post_campaign_post = EngagementCampaignPost()
            
        post_link = None

        post_campaign_post.campaign_linkedin_account = campaign_and_linkedin_account
        post_campaign_post.state = sequence
        post_campaign_post.state_status = "Performing"
        post_campaign_post.state_action_start_time = timezone.now()
        post_campaign_post.save()
        
        group_post = sequence.post_on == "Linkedin Group" and sequence.post_on_group
        
        if group_post:
            driver.get(sequence.post_on_group.url)
        else:
            
            feed_btn = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".global-nav__content>a")))
            feed_btn.click()
        
        sleep(give_totally_random_number_in_float())

        start_a_post_btn = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".share-box-feed-entry__closed-share-box button")))
        start_a_post_btn.click()

        sleep(give_totally_random_number_in_float(1, 4))

        post_description = WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".editor-content>div")))

        if sequence.post_text:
            post_description.send_keys(add_linkedin_account_info_in_text(
                sequence.post_text, campaign_and_linkedin_account.linkedin_account))
            sleep(give_totally_random_number_in_float(1, 4))
        
        if sequence.step == "image_post":
            post_an_image(driver, sequence)
        elif sequence.step == "video_post":
            post_an_video(driver, sequence)
        elif sequence.step == "document_post":
            post_an_document(driver, sequence)
        elif sequence.step == "poll_post":
            post_an_poll(driver, sequence)
        elif sequence.step == "event_post":
            post_an_event(driver, sequence)
        elif sequence.step == "hiring_post":
            post_an_job(driver, sequence)


        visibility = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".share-creation-state__comment-controls-container .share-state-change-button__button")))
        visibility.click()

        sleep(give_totally_random_number_in_float(1, 4))

        if sequence.visiblity == "Anyone":
            group_xpath = '//div[text()="Comments enabled"]'
            linkedin_profile_xpath = '//div[text()="Anyone can comment"]'
            
            anyone_option = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, group_xpath if group_post else linkedin_profile_xpath)))
            anyone_option.click()

        elif sequence.visiblity == "Connections Only":
            connections_only = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, '//div[text()="Connections who can view can also comment"]')))
            connections_only.click()

        elif sequence.visiblity == "No one":
            group_xpath = '//div[text()="Comments disabled"]'
            linkedin_profile_xpath = '//div[text()="No one can comment"]'
            
            no_one = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, group_xpath if group_post else linkedin_profile_xpath)))
            no_one.click()

        sleep(give_totally_random_number_in_float(1, 4))

        visiblity_save_btn = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '.share-box-footer__main-actions .ml2')))
        visiblity_save_btn.click()

        try:
            if visiblity_save_btn.get_attribute("disabled"):
                back_btn = WebDriverWait(driver, 4).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.share-box-footer__main-actions>button')))
                back_btn.click()
        except exceptions.StaleElementReferenceException as e:
            pass

        sleep(give_totally_random_number_in_float(3, 7))

        post_btn = WebDriverWait(driver, 4).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".share-actions__primary-action")))
        post_btn.click()
        
        sleep(give_totally_random_number_in_float(4, 10))
        
        
        try:
            close_btn = driver.find_element_by_css_selector("button[data-test-modal-close-btn]")
            close_btn.click()
            sleep(give_totally_random_number_in_float(1, 4))
        except exceptions.NoSuchElementException as e:
            pass
        except Exception as e:
            pass
        
        if sequence.step == "video_post":
            sleep(give_totally_random_number_in_float(120, 180))
        else:
            sleep(give_totally_random_number_in_float(60, 120))

        post_options_btn = WebDriverWait(driver, 4).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".feed-shared-control-menu__trigger")))
        post_options_btn.click()

        copy_link_of_post = WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.XPATH, '//h5[text()="Copy link to post"]')))
        copy_link_of_post.click()

        root = tk.Tk()
        root.withdraw()  # to hide the window
        post_link = root.clipboard_get()
        print(post_link)
        # except Exception as e:
        #     print(str(e))
        #     post_campaign_post.state_status = "Failed"
            
        if post_campaign_post.state_status != "Failed":
            post_campaign_post.state_status = "Finished"
            
        post_campaign_post.post_link = post_link
        post_campaign_post.state_action_finish_time = timezone.now()
        post_campaign_post.save()
        
        try:
            close_btn = driver.find_element_by_css_selector("button[data-test-modal-close-btn]")
            close_btn.click()
            sleep(give_totally_random_number_in_float(1, 3))
            discard_btn = driver.find_element_by_css_selector("button[data-test-dialog-primary-btn]")
            discard_btn.click()
            sleep(give_totally_random_number_in_float(1, 4))
        except exceptions.NoSuchElementException as e:
            pass
        except Exception as e:
            pass
        

def crawl_prospects_from_posts(driver, campaign_and_linkedin_account, posts):
    for post in posts:

        if not post.post_link:
            continue 
        
        driver.get(post.post_link)
        
        ### likes
        
        try:
            likes_count_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".social-details-social-counts__item .display-flex")))
            likes_count_btn.click()
            
            sleep(give_totally_random_number_in_float(7, 10))
            
            for i in range(1, 10000):
                
                try:
                    show_more_results = driver.find_element_by_css_selector(".scaffold-finite-scroll__load-button")
                    show_more_results.click()
                except exceptions.NoSuchElementException as e:
                    break
                except Exception as e:
                    pass
                
                sleep(give_totally_random_number_in_float(3, 5))
            
            prospects = driver.find_elements_by_css_selector(".social-details-reactors-tab-body__profile-link")
            
            for prospect in prospects:
                profile_link = prospect.get_attribute("href")
                
                if not "/in/" in profile_link:
                    continue
                
                name = prospect.find_element_by_css_selector(".artdeco-entity-lockup__title>span:nth-child(1)").text
                
                try:
                    headline = prospect.find_element_by_css_selector(".artdeco-entity-lockup__caption").text
                except exceptions.NoSuchElementException as e:
                    headline = ""
                    

                profile_link = f'{profile_link.split("?")[0]}/'

                prospect_data = {
                    "name": name,
                    "campaign_linkedin_account": campaign_and_linkedin_account,
                    "linkedin_profile_url": profile_link,
                }
                
                prospect_obj, created = Prospect.objects.get_or_create(**prospect_data)
                prospect_obj.headline = headline
                
                if prospect_obj.engagement:
                    prospect_obj.engagement= [*prospect_obj.engagement, "Liked Posts"]
                else:
                    prospect_obj.engagement= [ "Liked Posts" ]
                    
                prospect_obj.save()

            ### comments
            driver.find_element_by_css_selector("button[data-test-modal-close-btn]").click()
            
            sleep(give_totally_random_number_in_float(7, 10))
        except (exceptions.NoSuchElementException, exceptions.TimeoutException) as e:
            print(str(e), "no like btn found!!!!")
            
            
        try:
        
            for i in range(3):
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_DOWN)
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_DOWN)
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_UP)
                driver.find_element_by_xpath('//body').send_keys(Keys.END)
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_DOWN)
                driver.find_element_by_xpath('//body').send_keys(Keys.HOME)
                driver.find_element_by_xpath('//body').send_keys(Keys.PAGE_DOWN)
                driver.find_element_by_xpath('//body').send_keys(Keys.END)
                sleep(1)
            
            
            for i in range(1, 10000):
                
                try:
                    show_more_results = driver.find_element_by_css_selector(".comments-comments-list__load-more-comments-button")
                    show_more_results.click()
                except exceptions.NoSuchElementException as e:
                    break
                except Exception as e:
                    pass
                
                sleep(give_totally_random_number_in_float(3, 5))
            
            prospects = driver.find_elements_by_css_selector(".comments-comment-item__post-meta")
            
            for prospect in prospects:
                profile_link = prospect.find_element_by_css_selector(".comments-post-meta__profile-info-wrapper a").get_attribute("href")
                
                if not "/in/" in profile_link:
                    continue
                
                name = prospect.find_element_by_css_selector(".comments-post-meta__name-text").text
                
                try:
                    headline = prospect.find_element_by_css_selector(".comments-post-meta__headline").text
                except exceptions.NoSuchElementException as e:
                    headline = ""
                    

                profile_link = f'{profile_link.split("?")[0]}/'

                prospect_data = {
                    "name": name,
                    "campaign_linkedin_account": campaign_and_linkedin_account,
                    "linkedin_profile_url": profile_link,
                }
                
                prospect_obj, created = Prospect.objects.get_or_create(**prospect_data)
                prospect_obj.headline = headline
                
                if prospect_obj.engagement:
                    prospect_obj.engagement= [*prospect_obj.engagement, "Commented Posts"]
                else:
                    prospect_obj.engagement= [ "Commented Posts" ]
                    
                prospect_obj.save()

        except (exceptions.NoSuchElementException, exceptions.TimeoutException) as e:
            print(str(e), "no comment btn found!!!!")
            
        ### shares
        try:
            driver.execute_script('document.querySelector(".social-details-social-counts__item--with-social-proof:nth-child(3)>button").click()')
            sleep(give_totally_random_number_in_float(7, 10))
            
            for i in range(1, 10000):
                
                try:
                    show_more_results = driver.find_element_by_css_selector(".scaffold-finite-scroll__load-button")
                    show_more_results.click()
                except exceptions.NoSuchElementException as e:
                    break
                except Exception as e:
                    pass
                
                sleep(give_totally_random_number_in_float(3, 5))
            
            prospects = driver.find_elements_by_css_selector(".feed-shared-header__text-wrapper")
            
            for prospect in prospects:
                profile_link = prospect.find_element_by_css_selector(".feed-shared-text-view a").get_attribute("href")
                
                if not "/in/" in profile_link:
                    continue
                
                name = prospect.find_element_by_css_selector(".feed-shared-text-view a span").text

                profile_link = f'{profile_link.split("?")[0]}/'

                prospect_data = {
                    "name": name,
                    "campaign_linkedin_account": campaign_and_linkedin_account,
                    "linkedin_profile_url": profile_link,
                }
                
                prospect_obj, created = Prospect.objects.get_or_create(**prospect_data)
                
                if prospect_obj.engagement:
                    prospect_obj.engagement= [*prospect_obj.engagement, "Shared Posts"]
                else:
                    prospect_obj.engagement= [ "Shared Posts" ]
                prospect_obj.save()

            driver.find_element_by_css_selector("button[data-test-modal-close-btn]").click()
            
        except (exceptions.NoSuchElementException, exceptions.TimeoutException, exceptions.JavascriptException) as e:
            print(str(e), "no share btn found!!!!")
        # sleep(give_totally_random_number_in_float(30, 60))
        
        if post.state and post.state.step == "hiring_post":
            
            try:
                driver.execute_script('document.querySelector(".feed-shared-button").click()')
                
                sleep(give_totally_random_number_in_float(8, 15))
                
                job_id = driver.current_url.split("view/")[-1].split("/")[0]
                
                driver.get(f"https://www.linkedin.com/hiring/jobs/{job_id}/applicants/13166768963/detail/?r=UNRATED%2CGOOD_FIT%2CMAYBE")
                
                prospects = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".hiring-applicants__list-item a")))
                
                for prospect in prospects:
                    prospect.click()
                    sleep(give_totally_random_number_in_float())
                    
                    name = WebDriverWait(prospect, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".hiring-people-card__title"))).text
                    
                    
                    driver.execute_script("document.querySelector('.hiring-applicant-header-actions .ml1 button[aria-expanded=\"false\"]').click()")
                    
                    sleep(give_totally_random_number_in_float(3, 4))
                    profile_link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".artdeco-dropdown__content  li:nth-child(1) a"))).text

                    prospect_data = {
                        "name": name,
                        "campaign_linkedin_account": campaign_and_linkedin_account,
                        "linkedin_profile_url": profile_link,
                    }
                    
                    prospect_obj, created = Prospect.objects.get_or_create(**prospect_data)
                    
                    if prospect_obj.engagement:
                        prospect_obj.engagement = [*prospect_obj.engagement, "Job Applicant"]
                    else:
                        prospect_obj.engagement = [ "Job Applicant" ]
                        
                    prospect_obj.save()
            except (exceptions.NoSuchElementException, exceptions.TimeoutException, exceptions.JavascriptException) as e:
                print(str(e), "no attendee found!!!")
                
        elif post.state and post.state.step == "event_post":
            try:
                driver.execute_script('document.querySelector(".feed-shared-event__cta").click()')
                
                sleep(give_totally_random_number_in_float(15, 30))
                
                event_id = driver.current_url.split("events/")[-1].split("/")[0]
                
                driver.get(f"https://www.linkedin.com/events/{event_id}/comments/")
                
                manage_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".events-live-top-card__cta")))
                manage_btn.click()
                
                sleep(give_totally_random_number_in_float(1, 4))
                
                manage_attendees_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'li:nth-child(1) > div[role="button"]')))
                manage_attendees_btn.click()
                
                for i in range(1, 10000):
                
                    try:
                        show_more_results = driver.find_element_by_css_selector(".scaffold-finite-scroll__load-button")
                        show_more_results.click()
                    except exceptions.NoSuchElementException as e:
                        break
                    except Exception as e:
                        pass
                    
                    sleep(give_totally_random_number_in_float(3, 5))
                
                
                prospects = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".artdeco-list__item a")))
                
                for prospect in prospects:
                    sleep(give_totally_random_number_in_float(2, 4))
                    
                    name = WebDriverWait(prospect, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".artdeco-entity-lockup__title"))).text
                    
                    try:
                        headline = WebDriverWait(prospect, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle > span"))).text
                    except exceptions.TimeoutException as e:
                        headline = ""
                        
                    profile_link = prospect.get_attribute("href")

                    prospect_data = {
                        "name": name,
                        "campaign_linkedin_account": campaign_and_linkedin_account,
                        "linkedin_profile_url": profile_link,
                    }
                    
                    prospect_obj, created = Prospect.objects.get_or_create(**prospect_data)
                    
                    if prospect_obj.engagement:
                        prospect_obj.engagement = [*prospect_obj.engagement, "Event Attendee"]
                    else:
                        prospect_obj.engagement = [ "Event Attendee" ]
                        
                    prospect.headline = headline
                    prospect_obj.save()
            except (exceptions.NoSuchElementException, exceptions.TimeoutException, exceptions.JavascriptException) as e:
                print(str(e), "no attendee found!!!")

def crawl_prospects(driver, campaign_and_linkedin_account, user_account_is_salesnavigator):
    total_prospects_found = 0
    campaign_sequences = CampaignSequence.objects.filter(
        campaign=campaign_and_linkedin_account.campaign).order_by("order")

    campaign_sequence_first_step = campaign_sequences.first()

    for page in range(1 if not campaign_and_linkedin_account.campaign.pages_crawled else campaign_and_linkedin_account.campaign.pages_crawled + 1, campaign_and_linkedin_account.campaign.pages_crawled + settings.DAILY_PAGES_TO_CRAWL + 1):
        print(page)

        if total_prospects_found >= campaign_and_linkedin_account.campaign.crawl_total_prospects:
            break

        driver.get(generate_url(campaign_and_linkedin_account.campaign, page))

        sleep(give_totally_random_number_in_float())

        body = driver.find_element_by_tag_name("body").text

        if "No results found".lower() in body.lower():
            break

        if "Wait a few moments and try again.".lower() in body.lower():
            driver.get(generate_url(
                campaign_and_linkedin_account.campaign, page))

        if user_account_is_salesnavigator:

            sleep(give_totally_random_number_in_float(5, 8))

            try:
                select_sales_navigator_btn = driver.find_element_by_css_selector(
                    ".action-select-contract")
                select_sales_navigator_btn.click()
                sleep(give_totally_random_number_in_float(7, 10))
            except exceptions.NoSuchElementException:
                print("no contact chooser screen")
                pass

            try:
                scroll_bar_exists = driver.find_element_by_css_selector(
                    "._vertical-scroll-results_1igybl")
            except exceptions.NoSuchElementException:
                scroll_bar_exists = False

            if scroll_bar_exists:

                scroll_points = [round(x * 0.1, 1)
                                 for x in range(10, 1000)]  # from 1.0 to 99.9

                for scroll_times in range(2):

                    driver.execute_script(
                        f'document.querySelector("._vertical-scroll-results_1igybl").scrollTop = document.querySelector("._vertical-scroll-results_1igybl").scrollHeight/0')  # start

                    for i in scroll_points:
                        driver.execute_script(
                            f'document.querySelector("._vertical-scroll-results_1igybl").scrollTop = document.querySelector("._vertical-scroll-results_1igybl").scrollHeight/{i}')

                    driver.execute_script(
                        f'document.querySelector("._vertical-scroll-results_1igybl").scrollTop = document.querySelector("._vertical-scroll-results_1igybl").scrollHeight/1')  # end

            else:

                for i in range(10):
                    driver.find_element_by_xpath(
                        '//body').send_keys(Keys.PAGE_DOWN)
                    driver.find_element_by_xpath(
                        '//body').send_keys(Keys.PAGE_DOWN)
                    driver.find_element_by_xpath(
                        '//body').send_keys(Keys.PAGE_UP)

                driver.find_element_by_xpath('//body').send_keys(Keys.END)

                for i in range(10):
                    driver.find_element_by_xpath(
                        '//body').send_keys(Keys.PAGE_UP)
                    driver.find_element_by_xpath(
                        '//body').send_keys(Keys.PAGE_UP)
                    driver.find_element_by_xpath(
                        '//body').send_keys(Keys.PAGE_DOWN)

                driver.find_element_by_xpath('//body').send_keys(Keys.HOME)
                driver.find_element_by_xpath('//body').send_keys(Keys.END)

        sleep(give_totally_random_number_in_float())

        prospects_found, prospects = get_all_prospects_and_save_them_in_to_database(
            driver, campaign_and_linkedin_account, user_account_is_salesnavigator)

        total_prospects_found += prospects_found

        # if (
        #     not user_account_is_salesnavigator and
        #     prospects_found > 4 and
        #     campaign_sequences and
        #     campaign_sequence_first_step.step == "send_connection_request"
        # ):

        #     total_prospect_to_send_connection_request = [randint(
        #         0, prospects_found - 3) for i in range(10)]  # getting list of numbers # from 0 to maximum 7
        #     # choosing randomly from numbers to send connection request for example 6
        #     number_of_prospects_to_send_connection_request = chooseRandomly(
        #         *total_prospect_to_send_connection_request)

        #     for prospect in sample(prospects, number_of_prospects_to_send_connection_request):

        #         try:
        #             connect_btn = driver.find_element_by_css_selector(
        #                 f'button[aria-label="Invite {prospect.name} to connect"]')
        #             driver.execute_script(
        #                 "arguments[0].scrollIntoView({block: 'end', inline: 'nearest'});", connect_btn)
        #             sleep(give_totally_random_number_in_float())
        #             connect_btn.click()
        #         except exceptions.NoSuchElementException as e:
        #             continue

        #         prospect.state = campaign_sequence_first_step
        #         prospect.state_status = "Performing"
        #         prospect.state_action_start_time = timezone.now()
        #         prospect.save()

        #         prospect = send_connection_request_after_the_connection_btn_is_clicked(
        #             driver, campaign_sequence_first_step, prospect)

        #         prospect.state_action_finish_time = timezone.now()
        #         prospect.save()

        #         waitRandomly(
        #             {
        #                 "from": 8.2,
        #                 "to": 15.9,
        #             }, {
        #                 "from": 7.7,
        #                 "to": 12.5,
        #             }, {
        #                 "from": 6.89,
        #                 "to": 20.98,
        #             },
        #             {
        #                 "from": 4.898,
        #                 "to": 7.68,
        #             },
        #         )

    campaign_and_linkedin_account.campaign.pages_crawled = page
    campaign_and_linkedin_account.campaign.save()


def get_button_by_tag_name(driver, tag, btn_text):
    buttons = driver.find_elements_by_tag_name(tag)

    buttons = [btn for btn in buttons if btn_text in btn.text]

    if buttons:
        return buttons[0]

    return None


def get_buttons_by_tag_name(driver, tag, btn_text):
    buttons = driver.find_elements_by_tag_name(tag)

    buttons = [btn for btn in buttons if btn_text in btn.text]

    return buttons
