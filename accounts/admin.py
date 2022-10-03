from django.contrib import admin
from .models import UserProfile, Proxy, GoogleAccount , SmtpAccount, LinkedinAccount, License, Plan, ImportLinkedinAccount
# Register your models here.


class ProxyAdmin(admin.ModelAdmin):
    search_fields = ("server", "country__name",)
    list_filter = ("country",)
    list_display = ("country", "server", "port",)


admin.site.register(UserProfile)
admin.site.register(GoogleAccount)
admin.site.register(SmtpAccount)
admin.site.register(LinkedinAccount)

admin.site.register(Proxy, ProxyAdmin)
admin.site.register(License)
admin.site.register(Plan)
admin.site.register(ImportLinkedinAccount)