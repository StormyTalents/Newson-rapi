from django.db import models
from django.contrib.auth.models import User
from accounts.models import GoogleAccount, LinkedinAccount, SmtpAccount, UserProfile
from uuid import uuid4
from django.utils.timezone import now
from django.core.validators import FileExtensionValidator
from django.conf import settings
from multiselectfield import MultiSelectField


search_parameter_choices = (
    ("Country", "Country"),
    ("Connections", "Connections"),
    ("Headline", "Headline"),
)


status_choices = (
    ("Pending", "Pending"),
    ("Waiting For User Connections", "Waiting For User Connections"),
    ("Running", "Running"),
    ("Finished", "Finished"),
    ("Failed", "Failed"),
    ("Stopped", "Stopped"),
)


celery_task_status_choices = (
    ("Running", "Running"),
    ("Failed", "Failed"),
    ("Finished", "Finished"),
)


prospect_state_status_choices = (
    ("Performing", "Performing"),
    ("Failed", "Failed"),
    ("Finished", "Finished"),
)


outreach_step_choices = (
    ("send_connection_request", "Send Connection Request"),
    ("send_message", "Send Message"),
    ("send_inmail", "Send InMail"),
    ("like_3_posts", "Like 3 Posts"),
    ("follow", "Follow"),
    ("endorse_top_5_skills", "Endorse Top 5 Skills"),
    ("send_email", "Send Email"),
)

post_step_choices = (
    ("text_post", "Text Post"),
    ("image_post", "Image Post"),
    ("video_post", "Video Post"),
    ("document_post", "Document Post"),
    ("hiring_post", "Hiring Post"),
    ("poll_post", "Poll Post"),
    ("event_post", "Event Post"),
)

post_on_choices = (
    ("Linkedin Profile", "Linkedin Profile"),
    ("Linkedin Group", "Linkedin Group"),
)

job_post_workplace_type_choices = (
    ("On-site", "On-site"),
    ("Hybrid", "Hybrid"),
    ("Remote", "Remote"),
)

job_post_job_type_choices = (
    ("Full-time", "Full-time"),
    ("Part-time", "Part-time"),
    ("Contract", "Contract"),
    ("Temporary", "Temporary"),
    ("Other", "Other"),
    ("Volunteer", "Volunteer"),
    ("Internship", "Internship"),
)

poll_duration_choices = (
    ("1 day", "1 day"),
    ("3 days", "3 days"),
    ("1 weeks", "1 weeks"),
    ("2 weeks", "2 weeks"),
)

event_type_choices = (
    ("Online", "Online"),
    ("In person", "In person"),
)

event_format_choices = (
    ("LinkedIn Audio Event", "LinkedIn Audio Event"),
    ("LinkedIn Live", "LinkedIn Live"),
    ("External event link", "External event link"),
)

visibility_choices = (
    ("Anyone", "Anyone"),
    ("Connections Only", "Connections Only"),
    ("No one", "No one"),
)

method_choices = (
    ("Smtp", "Smtp"),
    ("Google Account", "Google Account"),
)

message_from_choices = (
    ("Prospect", "Prospect"),
    ("User", "User"),
)

platform_choices = (
    ("Linkedin", "Linkedin"),
    ("Linkedin Sales", "Linkedin Sales"),
)

prospect_action_choices = (
    ("send_connection_request", "Send Connection Request"),
    ("send_message", "Send Message"),
    ("send_inmail", "Send InMail"),
    ("like_3_posts", "Like 3 Posts"),
    ("follow", "Follow"),
    ("endorse_top_5_skills", "Endorse Top 5 Skills"),
    ("send_email", "Send Email"),
)

action_choices = (
    ("perform_campaign_actions", "perform_campaign_actions"),
    ("check_user_connections", "check_user_connections"),
    ("run_auto_accept_connection_requests", "run_auto_accept_connection_requests"),
    ("run_campaigns", "run_campaigns"),
    ("run_check_reply_and_get_conversations", "run_check_reply_and_get_conversations"),
)

campaign_types = (
    ("outreach", "outreach"),
    ("post", "post"),
)


engagement_choices = (
    ('Liked Posts', 'Liked Posts'),
    ('Commented Posts', 'Commented Posts'),
    ('Shared Posts', 'Shared Posts'),
    ('Job Applicant', 'Job Applicant'),
    ('Event Attendee', 'Event Attendee'),
)

event_timezone = (
    ("(UTC-12:00) International Date Line West", "(UTC-12:00) International Date Line West",),
    ("(UTC-11:00) Midway Island, Samoa", "(UTC-11:00) Midway Island, Samoa",),
    ("(UTC-10:00) Hawaii", "(UTC-10:00) Hawaii",),
    ("(UTC-09:30) Marquesas Islands", "(UTC-09:30) Marquesas Islands",),
    ("(UTC-09:00) Aleutian Islands", "(UTC-09:00) Aleutian Islands",),
    ("(UTC-08:00) Alaska", "(UTC-08:00) Alaska",),
    ("(UTC-08:00) Pitcairn Islands", "(UTC-08:00) Pitcairn Islands",),
    ("(UTC-07:00) Pacific Time (US and Canada), Tijuana", "(UTC-07:00) Pacific Time (US and Canada), Tijuana",),
    ("(UTC-07:00) Arizona", "(UTC-07:00) Arizona",),
    ("(UTC-06:00) Mountain Time (US and Canada)", "(UTC-06:00) Mountain Time (US and Canada)",),
    ("(UTC-06:00) Chihuahua, La Paz, Mazatlan", "(UTC-06:00) Chihuahua, La Paz, Mazatlan",),
    ("(UTC-06:00) Saskatchewan", "(UTC-06:00) Saskatchewan",),
    ("(UTC-06:00) Central America", "(UTC-06:00) Central America",),
    ("(UTC-05:00) Central Time (US and Canada)", "(UTC-05:00) Central Time (US and Canada)",),
    ("(UTC-05:00) Guadalajara, Mexico City, Monterrey", "(UTC-05:00) Guadalajara, Mexico City, Monterrey",),
    ("(UTC-05:00) Bogota, Lima, Quito", "(UTC-05:00) Bogota, Lima, Quito",),
    ("(UTC-04:00) Eastern Time (US and Canada)", "(UTC-04:00) Eastern Time (US and Canada)",),
    ("(UTC-04:00) Indiana (East)", "(UTC-04:00) Indiana (East)",),
    ("(UTC-04:00) Caracas, La Paz", "(UTC-04:00) Caracas, La Paz",),
    ("(UTC-04:00) Santiago", "(UTC-04:00) Santiago",),
    ("(UTC-03:00) Atlantic Time (Canada)", "(UTC-03:00) Atlantic Time (Canada)",),
    ("(UTC-03:00) Brasilia", "(UTC-03:00) Brasilia",),
    ("(UTC-03:00) Buenos Aires, Georgetown", "(UTC-03:00) Buenos Aires, Georgetown",),
    ("(UTC-02:30) Newfoundland and Labrador", "(UTC-02:30) Newfoundland and Labrador",),
    ("(UTC-02:00) Greenland", "(UTC-02:00) Greenland",),
    ("(UTC-02:00) Mid-Atlantic", "(UTC-02:00) Mid-Atlantic",),
    ("(UTC-01:00) Cape Verde Islands", "(UTC-01:00) Cape Verde Islands",),
    ("(UTC) Azores", "(UTC) Azores",),
    ("(UTC) Coordinated Universal Time", "(UTC) Coordinated Universal Time",),
    ("(UTC) Reykjavik", "(UTC) Reykjavik",),
    ("(UTC+01:00) Dublin, Edinburgh, Lisbon, London", "(UTC+01:00) Dublin, Edinburgh, Lisbon, London",),
    ("(UTC+01:00) Casablanca, Monrovia", "(UTC+01:00) Casablanca, Monrovia",),
    ("(UTC+01:00) West Central Africa", "(UTC+01:00) West Central Africa",),
    ("(UTC+02:00) Belgrade, Bratislava, Budapest, Ljubljana, Prague", "(UTC+02:00) Belgrade, Bratislava, Budapest, Ljubljana, Prague",),
    ("(UTC+02:00) Sarajevo, Skopje, Warsaw, Zagreb", "(UTC+02:00) Sarajevo, Skopje, Warsaw, Zagreb",),
    ("(UTC+02:00) Brussels, Copenhagen, Madrid, Paris", "(UTC+02:00) Brussels, Copenhagen, Madrid, Paris",),
    ("(UTC+02:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna", "(UTC+02:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna",),
    ("(UTC+02:00) Cairo", "(UTC+02:00) Cairo",),
    ("(UTC+02:00) Harare, Pretoria", "(UTC+02:00) Harare, Pretoria",),
    ("(UTC+03:00) Bucharest", "(UTC+03:00) Bucharest",),
    ("(UTC+03:00) Helsinki, Kiev, Riga, Sofia, Tallinn, Vilnius", "(UTC+03:00) Helsinki, Kiev, Riga, Sofia, Tallinn, Vilnius",),
    ("(UTC+03:00) Athens, Istanbul, Minsk", "(UTC+03:00) Athens, Istanbul, Minsk",),
    ("(UTC+03:00) Jerusalem", "(UTC+03:00) Jerusalem",),
    ("(UTC+03:00) Moscow, St. Petersburg, Volgograd", "(UTC+03:00) Moscow, St. Petersburg, Volgograd",),
    ("(UTC+03:00) Kuwait, Riyadh", "(UTC+03:00) Kuwait, Riyadh",),
    ("(UTC+03:00) Nairobi", "(UTC+03:00) Nairobi",),
    ("(UTC+03:00) Baghdad", "(UTC+03:00) Baghdad",),
    ("(UTC+04:00) Abu Dhabi, Muscat", "(UTC+04:00) Abu Dhabi, Muscat",),
    ("(UTC+04:00) Baku, Tbilisi, Yerevan", "(UTC+04:00) Baku, Tbilisi, Yerevan",),
    ("(UTC+04:30) Tehran", "(UTC+04:30) Tehran",),
    ("(UTC+04:30) Kabul", "(UTC+04:30) Kabul",),
    ("(UTC+05:00) Ekaterinburg", "(UTC+05:00) Ekaterinburg",),
    ("(UTC+05:00) Islamabad, Karachi, Tashkent", "(UTC+05:00) Islamabad, Karachi, Tashkent",),
    ("(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi", "(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi",),
    ("(UTC+05:30) Sri Jayawardenepura", "(UTC+05:30) Sri Jayawardenepura",),
    ("(UTC+05:45) Kathmandu", "(UTC+05:45) Kathmandu",),
    ("(UTC+06:00) Astana, Dhaka", "(UTC+06:00) Astana, Dhaka",),
    ("(UTC+06:00) Almaty, Novosibirsk", "(UTC+06:00) Almaty, Novosibirsk",),
    ("(UTC+06:30) Yangon Rangoon", "(UTC+06:30) Yangon Rangoon",),
    ("(UTC+07:00) Bangkok, Hanoi, Jakarta", "(UTC+07:00) Bangkok, Hanoi, Jakarta",),
    ("(UTC+07:00) Krasnoyarsk", "(UTC+07:00) Krasnoyarsk",),
    ("(UTC+08:00) Beijing, Chongqing, Hong Kong SAR, Urumqi", "(UTC+08:00) Beijing, Chongqing, Hong Kong SAR, Urumqi",),
    ("(UTC+08:00) Kuala Lumpur, Singapore", "(UTC+08:00) Kuala Lumpur, Singapore",),
    ("(UTC+08:00) Taipei", "(UTC+08:00) Taipei",),
    ("(UTC+08:00) Western Australia", "(UTC+08:00) Western Australia",),
    ("(UTC+08:00) Irkutsk, Ulaanbaatar", "(UTC+08:00) Irkutsk, Ulaanbaatar",),
    ("(UTC+08:45) Western Australia (Eucla)", "(UTC+08:45) Western Australia (Eucla)",),
    ("(UTC+09:00) Seoul", "(UTC+09:00) Seoul",),
    ("(UTC+09:00) Osaka, Sapporo, Tokyo", "(UTC+09:00) Osaka, Sapporo, Tokyo",),
    ("(UTC+09:00) Yakutsk", "(UTC+09:00) Yakutsk",),
    ("(UTC+09:30) Darwin", "(UTC+09:30) Darwin",),
    ("(UTC+09:30) Adelaide", "(UTC+09:30) Adelaide",),
    ("(UTC+10:00) Canberra, Melbourne, Sydney", "(UTC+10:00) Canberra, Melbourne, Sydney",),
    ("(UTC+10:00) Brisbane", "(UTC+10:00) Brisbane",),
    ("(UTC+10:00) Hobart", "(UTC+10:00) Hobart",),
    ("(UTC+10:00) Vladivostok", "(UTC+10:00) Vladivostok",),
    ("(UTC+10:00) Guam, Port Moresby", "(UTC+10:00) Guam, Port Moresby",),
    ("(UTC+10:30) Lord Howe", "(UTC+10:30) Lord Howe",),
    ("(UTC+11:00) Magadan, Solomon Islands, New Caledonia", "(UTC+11:00) Magadan, Solomon Islands, New Caledonia",),
    ("(UTC+11:00) Norfolk Island", "(UTC+11:00) Norfolk Island",),
    ("(UTC+12:00) Fiji Islands, Kamchatka, Marshall Islands", "(UTC+12:00) Fiji Islands, Kamchatka, Marshall Islands",),
    ("(UTC+12:00) Auckland, Wellington", "(UTC+12:00) Auckland, Wellington",),
    ("(UTC+12:00) Tarawa", "(UTC+12:00) Tarawa",),
    ("(UTC+12:45) Chatham Islands", "(UTC+12:45) Chatham Islands",),
    ("(UTC+13:00) Nuku'alofa", "(UTC+13:00) Nuku'alofa",),
    ("(UTC+14:00) Kiritimati", "(UTC+14:00) Kiritimati",),
)


class UserLinkedinGroup(models.Model):
    linkedin_account = models.ForeignKey(
        LinkedinAccount, on_delete=models.CASCADE)
    name = models.CharField(max_length=1024)
    url = models.URLField()
    group_urn = models.CharField(max_length=700)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ["linkedin_account", "url"]

    def __str__(self) -> str:
        return f"{self.linkedin_account.username} -> {self.name}"
    

class Label(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    description = models.TextField(blank = True, null = True)
    color = models.CharField(max_length=100, default = "#2A83EC")
    default_label = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name}"
    
    class Meta:
        unique_together = ["name", "user",]


class Campaign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    status = models.CharField(
        max_length=28, choices=status_choices, default="Pending")
    search_url = models.URLField(blank=True, null=True, max_length=900)
    crawl_total_prospects = models.SmallIntegerField(default=25)
    pages_crawled = models.SmallIntegerField(default=0)
    type = models.CharField(max_length=8, choices = campaign_types, default="outreach")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name}"


class CampaignLinkedinAccount(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    linkedin_account = models.ForeignKey(LinkedinAccount, on_delete=models.CASCADE)
    last_runned_at = models.DateTimeField(blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.linkedin_account.name}"


class PostSequence(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    order = models.SmallIntegerField(default=0)
    step = models.CharField(max_length=13, choices=post_step_choices)
    post_on = models.CharField(max_length=16, choices=post_on_choices, default="Linkedin Profile")
    post_on_group = models.ForeignKey(UserLinkedinGroup, on_delete=models.CASCADE, blank = True, null = True)
    post_text = models.TextField(blank=True, null=True, max_length=3000, help_text="For Any Post Type")
    
    image = models.ImageField(upload_to="post-images/", blank=True, null=True, help_text="For Posting A Post With An Image")
    image_alt_text = models.TextField(blank=True, null=True, max_length=300, help_text="For Post With An Image")
    
    video = models.FileField(
        upload_to='post-videos/', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mov','avi','mp4','webm','mkv'])]
    )
    video_thumbnail = models.ImageField(upload_to="post-video-thumbnails/", blank=True, null=True, help_text="For Posting A Post With A Video including thumbnail")
    
    document = models.FileField(
        upload_to='post-documents/', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['doc','docx','pdf','ppt','pptx'])]
    )
    document_title = models.CharField(blank=True, null=True, max_length=58, help_text="For Posting A Post With A Document Title * (Required)")
    
    job_title = models.CharField(blank=True, null=True, max_length=200, help_text="For Posting A Job Post With A Job Title * (Required)")
    job_company = models.CharField(blank=True, null=True, max_length=200, help_text="For Posting A Job Post With A Job Company * (Required)")
    job_workplace_type = models.CharField(max_length=7, choices=job_post_workplace_type_choices, blank = True, null = True)
    job_location = models.TextField(blank=True, null=True, max_length=486, help_text="For Posting A Job With A Job Location")
    employee_location = models.TextField(blank=True, null=True, max_length=486, help_text="For Posting A Job With A Employee Location")
    job_type = models.CharField(max_length=10, choices=job_post_job_type_choices, blank = True, null = True)
    job_description = models.CharField(max_length=10000, blank = True, null = True)
    
    poll_question = models.CharField(blank=True, null=True, max_length=140, help_text="For Posting A Poll With A Question * (Required)")
    option_1 = models.CharField(blank=True, null=True, max_length=30, help_text="For Posting A Poll With A Option 1 * (Required)")
    option_2 = models.CharField(blank=True, null=True, max_length=30, help_text="For Posting A Poll With A Option 2 * (Required)")
    option_3 = models.CharField(blank=True, null=True, max_length=30, help_text="For Posting A Poll With A Option 3")
    option_4 = models.CharField(blank=True, null=True, max_length=30, help_text="For Posting A Poll With A Option 4")
    poll_duration = models.CharField(max_length=7, choices=poll_duration_choices, blank = True, null = True)

    event_cover_image = models.ImageField(upload_to="event-cover-images/", blank=True, null=True, help_text="For Posting A Event With A Cover Image")
    event_format = models.CharField(blank=True, null=True, max_length=20, choices=event_format_choices, help_text="For Posting A Event With Event Format * (Required)")
    event_type = models.CharField(blank=True, null=True, max_length=9, choices=event_type_choices, help_text="For Posting A Event With Event Type * (Required)")
    event_name = models.CharField(blank=True, null=True, max_length=75, help_text="For Posting A Event With A Event Name * (Required)")
    event_timezone = models.CharField(blank=True, null=True, max_length=61, choices=event_timezone, help_text="For Posting A Event With A Timezone * (Required)")
    event_start_date_time = models.DateTimeField(blank=True, null=True, help_text="For Posting A Event With A Start Date Time * (Required)")
    event_end_date_time = models.DateTimeField(blank=True, null=True, help_text="For Posting A Event With A End Date Time")
    event_address = models.TextField(blank=True, null=True, max_length=486, help_text="For Posting A Event With A Address * (Required)")
    event_venue = models.TextField(blank=True, null=True, max_length=486, help_text="For Posting A Event With A Venue")
    event_external_event_link = models.URLField(blank=True, null=True, help_text="For Posting A Event With A External Link")
    event_description = models.CharField(max_length=5000, blank = True, null = True, help_text="For Posting A Event With A Description")
    event_speakers = models.CharField(max_length=500, blank = True, null = True, help_text="For Posting A Event With A Speaker")
    
    visiblity = models.CharField(max_length=16, choices = visibility_choices, default = "Anyone")
    delay_in_days = models.SmallIntegerField()
    delay_in_hours = models.SmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["order", "campaign"]

    def __str__(self) -> str:
        return f"{self.step}"


class EngagementCampaignPost(models.Model):
    campaign_linkedin_account = models.ForeignKey(CampaignLinkedinAccount, on_delete=models.CASCADE)
    post_link = models.URLField(blank=True, null = True)
    state = models.ForeignKey(PostSequence, on_delete=models.CASCADE, blank=True, null=True)
    state_status = models.CharField(max_length=40, choices=prospect_state_status_choices, blank=True, null=True)
    state_action_start_time = models.DateTimeField(blank=True, null=True)
    state_action_finish_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [ "campaign_linkedin_account", "state" ]

    def __str__(self) -> str:
        return f"{self.post_link}"


class CampaignSequence(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    order = models.SmallIntegerField(default=0)
    step = models.CharField(max_length=50, choices=outreach_step_choices)
    note = models.TextField(blank=True, null=True, max_length=299,
                            help_text="For Sending Connection Request")
    wait_for_connection_request_to_be_approved = models.BooleanField(default=True)
    message = models.TextField(
        blank=True, null=True, max_length=7999, help_text="For Sending Message")
    inmail_subject = models.TextField(
        blank=True, null=True, max_length=200, help_text="For Sending InMail Message")
    inmail_message = models.TextField(
        blank=True, null=True, max_length=486, help_text="For Sending InMail Message")
    smtp_account = models.ForeignKey(SmtpAccount, on_delete=models.SET_NULL, blank = True, null = True)
    google_account = models.ForeignKey(GoogleAccount, on_delete=models.SET_NULL, blank = True, null = True)
    from_email = models.EmailField(
        blank=True, null=True, help_text="For Sending Email Only For SMTP")
    email_subject = models.TextField(
        blank=True, null=True, max_length=200, help_text="For Sending Email")
    email_message = models.TextField(
        blank=True, null=True, max_length=700, help_text="For Sending Email")
    delay_in_days = models.SmallIntegerField()
    delay_in_hours = models.SmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["order", "campaign"]

    def __str__(self) -> str:
        return f"{self.step}"


class SearchParameter(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    parameter = models.CharField(
        max_length=30, choices=search_parameter_choices)
    value = models.CharField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.campaign.name} / {self.parameter}"


class Prospect(models.Model):
    campaign_linkedin_account = models.ForeignKey(CampaignLinkedinAccount, on_delete=models.CASCADE)
    entity_urn = models.CharField(max_length=700, blank = True, null = True)
    first_name = models.CharField(max_length=400, null = True)
    last_name = models.CharField(max_length=400, null = True)
    name = models.CharField(max_length=400)
    headline = models.CharField(max_length=1000, blank=True, null=True)
    occupation = models.CharField(max_length=700, blank=True, null=True)
    current_company = models.CharField(max_length=700, blank=True, null=True)
    school_university = models.CharField(max_length=700, blank=True, null=True)
    bio = models.TextField(blank = True, null = True)
    location = models.CharField(max_length=1000, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(blank=True, null=True, max_length=20)
    linkedin_profile_url = models.URLField(blank=True, null=True)
    linkedin_sales_navigator_profile_url = models.URLField(
        blank=True, null=True)
    linkedin_avatar = models.ImageField(
        upload_to="", blank=True, null=True)
    fully_crawled = models.BooleanField(default=False)
    connection_request_sent = models.BooleanField(default=False)
    connected = models.BooleanField(default=False)
    show_inside_inbox = models.BooleanField(default=False)
    engagement = MultiSelectField(choices = engagement_choices, blank = True, null = True)
    state = models.ForeignKey(
        CampaignSequence, on_delete=models.CASCADE, blank=True, null=True)
    state_status = models.CharField(
        max_length=40, choices=prospect_state_status_choices, blank=True, null=True)
    state_action_start_time = models.DateTimeField(blank=True, null=True)
    state_action_finish_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name}"
    
    @property
    def profile_id(self):
        
        if self.linkedin_profile_url:
            return self.linkedin_profile_url.split("/in/")[-1].split("/")[0]
        elif self.linkedin_sales_navigator_profile_url:
            return self.linkedin_sales_navigator_profile_url.split("/sales/lead/")[-1].split(",")[0]
        else:
            return None


class ProspectLabel(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name="prospect_labels")
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.label.name} / {self.prospect.name}"
    
    class Meta:
        unique_together = ["prospect", "label"]


class CampaignFailedReason(models.Model):
    reason = models.TextField()
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.campaign.name} -> {self.reason}"


class UserLinkedinConnection(models.Model):
    campaign = models.ForeignKey(
        CampaignLinkedinAccount, on_delete=models.SET_NULL, null=True)
    linkedin_account = models.ForeignKey(
        LinkedinAccount, on_delete=models.CASCADE)
    linkedin_profile_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ["linkedin_account", "linkedin_profile_url"]

    def __str__(self) -> str:
        return f"{self.linkedin_account.username} -> {self.linkedin_profile_url}"


class CeleryJob(models.Model):
    task_id = models.UUIDField()
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=celery_task_status_choices, default="Running")

    def __str__(self) -> str:
        return f"{self.task_id}  // {self.campaign.name}"


class Room(models.Model):
    linkedin_account = models.ForeignKey(LinkedinAccount, on_delete=models.CASCADE, null = True)
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, null = True)
    message_thread = models.URLField()
    customer_message_readed = models.IntegerField(default=0)
    platform = models.CharField(max_length=14, choices=platform_choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.prospect.name if self.prospect else 'No Name'}"
    
    class Meta:
        unique_together = ["linkedin_account", "message_thread", "platform", ]


class Message(models.Model):
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="messages")
    message_from = models.CharField(max_length=8, choices=message_from_choices)
    time = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.room.prospect.name if self.room.prospect else 'No Name'}"


class EmailWebHook(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, unique = True)
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.id} - {self.prospect.name if self.prospect else 'No Name'} - {self.prospect.email if self.prospect else 'No Email'}"


class ProspectActionLog(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, unique = True)
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    action = models.CharField(max_length=23, choices = prospect_action_choices, blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.id} - {self.prospect.name if self.prospect else 'No Name'} - {self.action}"


class CeleryJobsLog(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, unique = True)
    celery_job = models.UUIDField()
    started_at = models.DateTimeField(default=now)
    finished_at = models.DateTimeField(blank = True, null = True)
    error = models.BooleanField(default=False)
    error_message = models.TextField(blank = True, null = True)
    action = models.CharField(max_length=37, choices = action_choices)
    
    def __str__(self) -> str:
        return f"{self.celery_job} - {self.started_at} - {self.action}"