from accounts.models import ImportLinkedinAccount, LinkedinAccount, UserProfile
from base.models import Country
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from django.conf import settings
from base.utils import start_driver, give_totally_random_number_in_float, chooseRandomly, waitRandomly
from accounts.api.utils import connect_linkedin_account_with_automatic_verification
import json
from django.utils import timezone
from celery.decorators import task


@task(name="import_linkedin_accounts", time_limit=82800, soft_time_limit=82800)
def import_linkedin_accounts(userprofile_id, import_linkeidn_account_id, linkedin_accounts_to_connect):
    userprofile = UserProfile.objects.filter(id = userprofile_id).first()
    instance = ImportLinkedinAccount.objects.filter(id = import_linkeidn_account_id).first()
    instance.imported = instance.total_rows
    failed_rows = []
    
    for index, linkedin_account_to_connect in enumerate(linkedin_accounts_to_connect):
        
        if LinkedinAccount.objects.filter(
            username = linkedin_account_to_connect["Linkedin Email *"],
            profile = userprofile,
        ).exists():
            instance.failed += 1
            instance.imported -= 1
            failed_rows.append({
                "row": index + 2,
                "reason": "Linkedin account with same username already exists in user profile!",
                "error_message": "UniqueUsernameError",
            })
            continue
        
        country = Country.objects.filter(name = linkedin_account_to_connect["Country *"]).first()
        
        if not country or not country.proxy_set.filter(linkedin_proxy__isnull=True).first():
            instance.failed += 1
            instance.imported -= 1
            failed_rows.append({
                "row": index + 2,
                "reason": "Country or Proxy Doesn't Exist!",
            })
            continue
            
        proxy = country.proxy_set.filter(linkedin_proxy__isnull=True).first()

        driver, success = start_driver(action="import_linkedin_accounts", proxy = proxy)
        
        failed, reason, error_message = connect_linkedin_account_with_automatic_verification(driver, linkedin_account_to_connect, userprofile, proxy)
        
        if failed:
            instance.failed += 1
            instance.imported -= 1
            failed_rows.append({
                "row": index + 2,
                "reason": reason,
                "error_message": error_message,
            })
            
        driver.quit()
        
    instance.finished = True
    instance.finished_at = timezone.now()
    instance.failed_rows = json.dumps(failed_rows)
    instance.save()