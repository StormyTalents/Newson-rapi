from uuid import uuid4
from celery.decorators import task, periodic_task
from main.models import Campaign, PostSequence, Prospect, CampaignFailedReason, UserLinkedinConnection, CeleryJob, CampaignSequence, Message, CampaignLinkedinAccount, CeleryJobsLog, EngagementCampaignPost, UserLinkedinGroup
from accounts.models import UserProfile, LinkedinAccount
from django.contrib.auth.models import User
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common import exceptions
from time import sleep
from datetime import timedelta, datetime
from .utils import (fill_in_details_of_prospects_and_perform_the_step, check_salesnavigator, check_reply_and_get_conversations_for_linkedin_messaging,
                    action_to_do_if_cookie_failed_for_campaign, get_element_with_possibilities, get_action_limits,
                    get_button_by_tag_name, send_message, crawl_prospects, send_messages, like_3_posts, follows, endorse_top_5_skills,
                    send_connection_requests, send_inmails, send_emails, send_message_in_linkedin_messaging,
                    check_reply_and_get_conversations_for_linkedin_sales_messaging, send_message_in_linkedin_sales_messaging,
                    check_if_actions_can_run_for_a_linkedin_account, auto_accept_connection_requests, add_linkedin_account_info_in_text,
                    post_posts_on_linkedin_account, crawl_prospects_from_posts)
from django.conf import settings
from base.utils import start_driver, give_totally_random_number_in_float, chooseRandomly, waitRandomly, get_proxy_options
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions as excep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.utils import timezone
from celery.task.control import revoke
import tkinter as tk
from http.cookies import SimpleCookie
import requests
from django.db.models import Q
import urllib.parse


@task(name="run_post_campaign", time_limit=82800, soft_time_limit=82800)
def run_post_campaign(campaign_id, user_id):
    campaign = Campaign.objects.filter(id=campaign_id).first()
    user = User.objects.filter(id=user_id).first()

    if not campaign:
        return "Campaign Doesn't Exist!"

    if not user:
        return "User Doesn't Exist!"

    if campaign.type != "post":
        return "Campaign Isn't Post Campaign!"

    campaign.status = "Running"
    campaign.save()

    campaign_linkedin_accounts = CampaignLinkedinAccount.objects.filter(
        campaign=campaign,
        linkedin_account__isnull=False,
        linkedin_account__connected=True,
        linkedin_account__ready_for_use=True
    ).distinct()

    new_campaign_linkedin_accounts = []

    for campaign_and_linkedin_account in campaign_linkedin_accounts:

        if not check_if_actions_can_run_for_a_linkedin_account(campaign_and_linkedin_account.linkedin_account):
            print("Can't Perform An Action For This Account!!")
            continue

        new_campaign_linkedin_accounts.append(campaign_and_linkedin_account)

    for campaign_and_linkedin_account in new_campaign_linkedin_accounts:

        driver, success = start_driver(
            campaign_and_linkedin_account.linkedin_account,
            lambda: action_to_do_if_cookie_failed_for_campaign(campaign),
            "run_post_campaign",
        )

        if not success:
            driver.quit()
            return

        post_posts_on_linkedin_account(driver, campaign_and_linkedin_account)

        driver.quit()

    return "Success"


@task(name="run_outreach_campaign", time_limit=82800, soft_time_limit=82800)
def run_outreach_campaign(campaign_id, user_id, send_total_connection_requests=None):
    campaign = Campaign.objects.filter(id=campaign_id).first()
    user = User.objects.filter(id=user_id).first()

    if not campaign:
        return "Campaign Doesn't Exist!"

    if not user:
        return "User Doesn't Exist!"

    if campaign.type != "outreach":
        return "Campaign Isn't Outreach Campaign!"

    # for campaign_and_linkedin_account in CampaignLinkedinAccount.objects.filter(campaign=campaign, linkedin_account__connected = True, linkedin_account__ready_for_use = True):
    #     connections = UserLinkedinConnection.objects.filter(linkedin_account=campaign_and_linkedin_account.linkedin_account)

    #     if not connections:
    #         campaign.status = "Waiting For User Connections"
    #         campaign.save()

    #         return "Waiting For User Connections To Be Added!"

    campaign.status = "Running"
    campaign.save()

    user_profile = user.userprofile
    campaign_linkedin_accounts = CampaignLinkedinAccount.objects.filter(
        campaign=campaign, linkedin_account__isnull=False, linkedin_account__connected=True, linkedin_account__ready_for_use=True).distinct()
    new_campaign_linkedin_accounts = []

    for campaign_and_linkedin_account in campaign_linkedin_accounts:

        if not check_if_actions_can_run_for_a_linkedin_account(campaign_and_linkedin_account.linkedin_account):
            print("Can't Perform An Action For This Account!!")
            continue

        if (
            campaign_and_linkedin_account.last_runned_at and
            not campaign_and_linkedin_account.last_runned_at.date() < timezone.now().date()
        ):
            print(
                f"The Campaign Already Ran Today For {campaign_and_linkedin_account.linkedin_account.username}!")
            continue

        campaign_and_linkedin_account.last_runned_at = timezone.now()
        campaign_and_linkedin_account.save()
        new_campaign_linkedin_accounts.append(campaign_and_linkedin_account)

    for campaign_and_linkedin_account in new_campaign_linkedin_accounts:

        driver, success = start_driver(
            campaign_and_linkedin_account.linkedin_account,
            lambda: action_to_do_if_cookie_failed_for_campaign(campaign),
            "run_outreach_campaign",
        )

        if not success:
            driver.quit()
            return

        if "/sales/" in campaign.search_url and not check_salesnavigator(driver):
            driver.quit()
            return "Success"

        user_account_is_salesnavigator = True if "/sales/" in campaign.search_url else False

        if Prospect.objects.filter(campaign_linkedin_account__campaign=campaign).count() < campaign.crawl_total_prospects:
            crawl_prospects(driver, campaign_and_linkedin_account,
                            user_account_is_salesnavigator)

        campaign_failed = False
        error_messages = []

        cookie = SimpleCookie()
        cookie.load(
            campaign_and_linkedin_account.linkedin_account.header_cookie)
        cookies = {k: v.value for k, v in cookie.items()}
        headers = {
            "Csrf-Token": campaign_and_linkedin_account.linkedin_account.header_csrf_token}
        proxies = get_proxy_options(
            campaign_and_linkedin_account.linkedin_account.proxy)["proxy"]

        for retry in range(5):
            try:
                prospects = Prospect.objects.filter(campaign_linkedin_account=campaign_and_linkedin_account, fully_crawled=False)[
                    :get_action_limits(campaign_and_linkedin_account, "fully_crawl")]
                fill_in_details_of_prospects_and_perform_the_step(
                    driver, campaign_and_linkedin_account, user_account_is_salesnavigator, prospects, cookies, headers, proxies)
                campaign_failed = False
                break
            except Exception as e:
                campaign_failed = True
                print(str(e))
                error_messages.append(str(e))

        if campaign_failed:
            campaign.status = "Failed"

            for error_msg in error_messages:
                CampaignFailedReason.objects.create(
                    reason=error_msg, campaign=campaign)

        sleep(give_totally_random_number_in_float())

        driver.quit()

    return "Success"


@periodic_task(run_every=timedelta(hours=1), time_limit=3300, soft_time_limit=3300, bind=True)
def crawl_post_campaign_prospects(self, user_id=None, initial={"connected": True, "ready_for_use": True}, override_profile_arguments=[]):
    current_time_1Halfhours_behind = timezone.now() - timedelta(minutes=90)

    if CeleryJobsLog.objects.filter(started_at__gt=current_time_1Halfhours_behind, finished_at__isnull=True, action="crawl_post_campaign_prospects").exists():
        return print("The Previous job hasn't finished yet!")

    job = CeleryJobsLog.objects.create(
        celery_job = self.request.id,
        # celery_job=uuid4(),
        action="crawl_post_campaign_prospects",
        started_at=timezone.now(),
    )

    rotten_jobs = CeleryJobsLog.objects.filter(
        started_at__lte=current_time_1Halfhours_behind, finished_at__isnull=True, action="crawl_post_campaign_prospects").all()

    for job in rotten_jobs:
        revoke(job.celery_job, terminate=True)

    rotten_jobs.delete()

    try:

        linkedin_account_filter = initial

        if user_id:
            linkedin_account_filter["profile__user_id"] = user_id

        linkedin_accounts = LinkedinAccount.objects.filter(
            **linkedin_account_filter).order_by("profile").distinct()

        for linkedin_account in linkedin_accounts:

            for argument in override_profile_arguments:
                setattr(linkedin_account, argument["key"], argument["value"])

            if not check_if_actions_can_run_for_a_linkedin_account(linkedin_account):
                continue

            driver, success = start_driver(
                linkedin_account, action="crawl_post_campaign_prospects")

            if not success:
                driver.quit()
                continue

            sleep(give_totally_random_number_in_float())

            for campaign in Campaign.objects.filter(user=linkedin_account.profile.user, type="post").exclude(status="Stopped"):

                sequences = PostSequence.objects.filter(
                    campaign=campaign).order_by("order")

                campaign_linkedin_account = CampaignLinkedinAccount.objects.filter(
                    campaign=campaign,
                    linkedin_account=linkedin_account,
                ).first()

                posted_posts = EngagementCampaignPost.objects.filter(
                    campaign_linkedin_account=campaign_linkedin_account,
                )

                crawl_prospects_from_posts(
                    driver, campaign_linkedin_account, posted_posts)

            driver.quit()

    except Exception as e:
        job.error = True
        job.error_message = f"{e}"

    job.finished_at = timezone.now()
    job.save()

    return "Success"


@periodic_task(run_every=timedelta(hours=1), time_limit=3300, soft_time_limit=3300, bind=True)
def perform_campaign_actions(self, user_id=None, initial={"connected": True, "ready_for_use": True}, override_profile_arguments=[]):

    current_time_1Halfhours_behind = timezone.now() - timedelta(minutes=90)

    if CeleryJobsLog.objects.filter(started_at__gt=current_time_1Halfhours_behind, finished_at__isnull=True, action="perform_campaign_actions").exists():
        return print("The Previous job hasn't finished yet!")

    job = CeleryJobsLog.objects.create(
        celery_job=self.request.id,
        action="perform_campaign_actions",
        started_at=timezone.now(),
    )

    rotten_jobs = CeleryJobsLog.objects.filter(
        started_at__lte=current_time_1Halfhours_behind, finished_at__isnull=True, action="perform_campaign_actions").all()

    for job in rotten_jobs:
        revoke(job.celery_job, terminate=True)

    rotten_jobs.delete()

    try:

        linkedin_account_filter = initial

        if user_id:
            linkedin_account_filter["profile__user_id"] = user_id

        linkedin_accounts = LinkedinAccount.objects.filter(
            **linkedin_account_filter).order_by("profile").distinct()

        for linkedin_account in linkedin_accounts:

            for argument in override_profile_arguments:
                setattr(linkedin_account, argument["key"], argument["value"])

            if not check_if_actions_can_run_for_a_linkedin_account(linkedin_account):
                continue

            driver, success = start_driver(
                linkedin_account, action="perform_campaign_actions")

            if not success:
                driver.quit()
                continue

            sleep(give_totally_random_number_in_float())

            cookie = SimpleCookie()
            cookie.load(linkedin_account.header_cookie)
            cookies = {k: v.value for k, v in cookie.items()}
            headers = {"Csrf-Token": linkedin_account.header_csrf_token}
            proxies = get_proxy_options(linkedin_account.proxy)["proxy"]

            for campaign in Campaign.objects.filter(user=linkedin_account.profile.user).exclude(status="Stopped"):

                sequences = CampaignSequence.objects.filter(
                    campaign=campaign).order_by("order")

                campaign_linkedin_account = CampaignLinkedinAccount.objects.filter(
                    campaign=campaign,
                    linkedin_account=linkedin_account,
                ).first()

                user_account_is_salesnavigator = True if "/sales/" in campaign.search_url else False

                prospects = Prospect.objects.filter(
                    campaign_linkedin_account=campaign_linkedin_account,
                    fully_crawled=False
                )[:get_action_limits(campaign_linkedin_account, "fully_crawl")]

                for sequence in sequences:

                    if sequence.step == "send_connection_request":
                        print("send_connection_requests")
                        send_connection_requests(
                            sequence, campaign_linkedin_account, cookies, headers, proxies)

                    elif sequence.step == "send_message":
                        send_messages(driver, sequence,
                                      campaign_linkedin_account)

                    elif sequence.step == "send_inmail":
                        send_inmails(driver, sequence,
                                     campaign_linkedin_account)

                    elif sequence.step == "like_3_posts":
                        like_3_posts(driver, sequence,
                                     campaign_linkedin_account)

                    elif sequence.step == "follow":
                        follows(driver, sequence, campaign_linkedin_account)

                    elif sequence.step == "endorse_top_5_skills":
                        endorse_top_5_skills(
                            driver, sequence, campaign_linkedin_account)

                    elif sequence.step == "send_email":
                        send_emails(sequence, campaign_linkedin_account)

                for retry in range(2):
                    try:
                        fill_in_details_of_prospects_and_perform_the_step(
                            driver, campaign_linkedin_account, user_account_is_salesnavigator, prospects, cookies, headers, proxies)
                        break
                    except Exception as e:
                        print(
                            "\n\n Error in fill_in_details_of_prospects_and_perform_the_step of perform actions \n\n")
                        print(str(e))

            driver.quit()

    except Exception as e:
        job.error = True
        job.error_message = f"{e}"

    job.finished_at = timezone.now()
    job.save()

    return "Success"


# @task(name="check_user_connections")
@periodic_task(run_every=timedelta(hours=1), time_limit=3000, soft_time_limit=3000)
def check_user_connections(user_id=None, initial={"connected": True, "ready_for_use": True}, override_profile_arguments=[]):

    print("HERE", "check_user_connections")

    linkedin_account_filter = initial

    if user_id:
        linkedin_account_filter["profile__user_id"] = user_id
        
    linkedin_account_filter["header_csrf_token__isnull"] = False
    linkedin_account_filter["header_cookie__isnull"] = False

    linkedin_accounts = LinkedinAccount.objects.filter(
        **linkedin_account_filter).order_by("profile").exclude(
            header_csrf_token="",
            header_cookie=""
    ).distinct()

    for linkedin_account in linkedin_accounts:

        for argument in override_profile_arguments:
            setattr(linkedin_account, argument["key"], argument["value"])

        cookie = SimpleCookie()
        cookie.load(linkedin_account.header_cookie)
        cookies = {k: v.value for k, v in cookie.items()}
        headers = {"Csrf-Token": linkedin_account.header_csrf_token}
        start_ = 0
        prospects_exist_in_campaigns = 0

        while True:

            if prospects_exist_in_campaigns > 35:
                print("No new connections")
                break

            url = f'https://www.linkedin.com/voyager/api/relationships/dash/connections?decorationId=com.linkedin.voyager.dash.deco.web.mynetwork.ConnectionListWithProfile-15&count=40&q=search&sortType=RECENTLY_ADDED&start={start_}'
            response = requests.get(url, cookies=cookies, headers=headers, proxies=get_proxy_options(
                linkedin_account.proxy)["proxy"])
            
            response = response.json()['elements']

            if not response:
                break

            for prospect in response:
                try:
                    prospect_info = prospect["connectedMemberResolutionResult"]
                except KeyError as e:
                    continue

                profile_url = f"https://www.linkedin.com/in/{prospect_info['publicIdentifier']}/"
                profile_url2 = f"https://www.linkedin.com/in/{prospect_info['entityUrn'].split('fsd_profile:')[-1]}/"

                if not UserLinkedinConnection.objects.filter(linkedin_account=linkedin_account, linkedin_profile_url=profile_url).first():
                    UserLinkedinConnection.objects.create(
                        linkedin_account=linkedin_account,
                        linkedin_profile_url=profile_url
                    )
                    prospects_exist_in_campaigns = 0
                else:
                    prospects_exist_in_campaigns += 1

                prospect_instances = Prospect.objects.filter(
                    Q(linkedin_profile_url=profile_url) | Q(
                        linkedin_profile_url=profile_url2),
                    Q(connected=False) | Q(connection_request_sent=False),
                    campaign_linkedin_account__linkedin_account=linkedin_account,

                ).distinct()

                for instance in prospect_instances:
                    instance.connected = True
                    instance.connection_request_sent = True
                    instance.save()

            start_ += 40

            sleep(give_totally_random_number_in_float(20, 30))

        for connection in UserLinkedinConnection.objects.filter(linkedin_account=linkedin_account).all():

            prospect_instances = Prospect.objects.filter(
                Q(connected=False) | Q(connection_request_sent=False),
                campaign_linkedin_account__linkedin_account=linkedin_account,
                linkedin_profile_url=connection.linkedin_profile_url
            ).distinct()

            for prospect in prospect_instances:
                prospect.connected = True
                prospect.connection_request_sent = True
                prospect.save()


@periodic_task(run_every=timedelta(hours=1), time_limit=3000, soft_time_limit=3000)
def check_user_groups(user_id=None, initial={"connected": True, "ready_for_use": True}, override_profile_arguments=[]):

    print("HERE", "check_user_groups")

    linkedin_account_filter = initial

    if user_id:
        linkedin_account_filter["profile__user_id"] = user_id

    linkedin_accounts = LinkedinAccount.objects.filter(
        **linkedin_account_filter).order_by("profile").distinct()

    for linkedin_account in linkedin_accounts:

        for argument in override_profile_arguments:
            setattr(linkedin_account, argument["key"], argument["value"])

        cookie = SimpleCookie()
        cookie.load(linkedin_account.header_cookie)
        cookies = {k: v.value for k, v in cookie.items()}
        headers = {"Csrf-Token": linkedin_account.header_csrf_token}
        proxies = get_proxy_options(linkedin_account.proxy)["proxy"]
        profile_urn_in_http_format = urllib.parse.quote_plus(
            linkedin_account.profile_urn)
        start_ = 0
        group_exists = 0

        while True:

            if group_exists > 35:
                print("No new groups")
                break

            url = f'https://www.linkedin.com/voyager/api/voyagerGroupsDashGroups?decorationId=com.linkedin.voyager.dash.deco.groups.GroupListingPage-2&count=10&membershipStatuses=List(MEMBER,MANAGER,OWNER)&profileUrn={profile_urn_in_http_format}&q=member&start={start_}'
            response = requests.get(
                url, cookies=cookies, headers=headers, proxies=proxies)
            response = response.json()['elements']

            if not response:
                print("no new groups")
                break

            for group in response:
                group_name = group["name"]
                group_entity_urn = group["entityUrn"]
                group_id = group_entity_urn.split('fsd_group:')[-1]
                group_url = f"https://www.linkedin.com/groups/{group_id}/"

                if not UserLinkedinGroup.objects.filter(linkedin_account=linkedin_account, url=group_url).first():
                    UserLinkedinGroup.objects.create(
                        linkedin_account=linkedin_account,
                        name=group_name,
                        url=group_url,
                        group_urn=group_entity_urn,
                    )
                    group_exists = 0
                else:
                    group_exists += 1

            start_ += 40

            sleep(give_totally_random_number_in_float(20, 30))


@periodic_task(run_every=timedelta(hours=1), time_limit=3000, soft_time_limit=3000)
def run_auto_accept_connection_requests(user_id=None, initial={"connected": True, "ready_for_use": True, "auto_accept_connection_requests": True}, override_profile_arguments=[]):
    linkedin_account_filter = initial

    if user_id:
        linkedin_account_filter["profile__user_id"] = user_id

    linkedin_accounts = LinkedinAccount.objects.filter(
        **linkedin_account_filter).order_by("profile").distinct()
    new_linkedin_accounts = []

    for linkedin_account in linkedin_accounts:

        for argument in override_profile_arguments:
            setattr(linkedin_account, argument["key"], argument["value"])

        if not check_if_actions_can_run_for_a_linkedin_account(linkedin_account):
            continue

        if (
            linkedin_account.auto_accept_connection_requests_last_ran and
            not linkedin_account.auto_accept_connection_requests_last_ran.date() < timezone.now().date()
        ):
            print(
                f"The Auto Accept Connection Request Already Ran Today For {linkedin_account.username}!")
            continue

        linkedin_account.auto_accept_connection_requests_last_ran = timezone.now()
        linkedin_account.save()
        new_linkedin_accounts.append(linkedin_account)

    for linkedin_account in new_linkedin_accounts:

        driver, success = start_driver(
            linkedin_account, action="run_auto_accept_connection_requests")

        if not success:
            driver.quit()
            continue

        sleep(give_totally_random_number_in_float())

        auto_accept_connection_requests(driver, linkedin_account)

        driver.quit()


@periodic_task(run_every=timedelta(minutes=15), time_limit=840, soft_time_limit=840)
def run_campaigns(user_id=None, initial={}, override_profile_arguments=[]):
    profile_filter = initial

    if user_id:
        profile_filter["profile__user_id"] = user_id

    user_profiles = UserProfile.objects.filter(**profile_filter)

    for profile in user_profiles:

        for argument in override_profile_arguments:
            setattr(profile, argument["key"], argument["value"])

        campaigns = Campaign.objects.filter(
            user=profile.user, campaignlinkedinaccount__isnull=False, campaignlinkedinaccount__linkedin_account__connected=True, campaignlinkedinaccount__linkedin_account__ready_for_use=True).exclude(status="Finished").all().distinct()

        if not campaigns:
            continue

        connection_request_per_campaign = round(
            (settings.DAILY_PAGES_TO_CRAWL*10)/len(campaigns))

        for campaign in campaigns:

            if campaign.type == "outreach":
                task = run_outreach_campaign.delay(campaign.id, profile.user.id,
                                                   connection_request_per_campaign)
            elif campaign.type == "post":
                task = run_post_campaign.delay(campaign.id, profile.user.id)

            CeleryJob.objects.create(
                task_id=f"{task.task_id}", campaign=campaign)

    return "Success"


@periodic_task(run_every=timedelta(hours=1), time_limit=3000, soft_time_limit=3000, bind=True)
def run_check_reply_and_get_conversations(self, user_id=None, initial={"connected": True, "ready_for_use": True}, override_profile_arguments=[]):

    current_time_1Halfhours_behind = timezone.now() - timedelta(minutes = 90)

    if CeleryJobsLog.objects.filter(started_at__gt = current_time_1Halfhours_behind, finished_at__isnull=True, action = "run_check_reply_and_get_conversations").exists():
        return print("The Previous job hasn't finished yet!")

    job = CeleryJobsLog.objects.create(
        celery_job = self.request.id,
        # celery_job = uuid4(),
        action = "run_check_reply_and_get_conversations",
        started_at = timezone.now(),
    )

    rotten_jobs = CeleryJobsLog.objects.filter(started_at__lte = current_time_1Halfhours_behind, finished_at__isnull=True, action = "run_check_reply_and_get_conversations").all()

    for job in rotten_jobs:
        revoke(job.celery_job, terminate=True)

    rotten_jobs.delete()

    try:
        linkedin_account_filter = initial

        if user_id:
            linkedin_account_filter["profile__user_id"] = user_id

        linkedin_accounts = LinkedinAccount.objects.filter(
            **linkedin_account_filter).order_by("profile").distinct()

        for linkedin_account in linkedin_accounts:

            for argument in override_profile_arguments:
                setattr(linkedin_account, argument["key"], argument["value"])

            driver, success = start_driver(
                linkedin_account, action="run_check_reply_and_get_conversations")

            sleep(give_totally_random_number_in_float())

            if not success:
                driver.quit()
                continue
            
            if not check_salesnavigator(driver):
                driver.quit()
                continue

            try:
                check_reply_and_get_conversations_for_linkedin_messaging(
                    driver, linkedin_account)  # linkedin messaging
            except Exception as e:
                print(e)
                print(linkedin_account, "Not Working The Linkedin Messages")

            try:
                check_reply_and_get_conversations_for_linkedin_sales_messaging(
                    driver, linkedin_account)  # linkedin Sales Messaging
            except Exception as e:
                print(e)
                print(linkedin_account, "Not Working The Linkedin Sales Messages")

            driver.quit()
    except Exception as e:
        job.error = True
        job.error_message = f"{e}"

    job.finished_at = timezone.now()
    job.save()


@task(name="send_message", time_limit=600, soft_time_limit=600)
def send_message(message_id):
    message = Message.objects.filter(id=message_id).first()

    driver, success = start_driver(
        message.room.linkedin_account, action="send_message")

    if not success:
        driver.quit()
        return

    if message.room.platform == "Linkedin":
        send_message_in_linkedin_messaging(
            driver, message)  # linkedin messaging
    else:
        send_message_in_linkedin_sales_messaging(
            driver, message)  # linkedin messaging

    driver.quit()
