from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import Account, CustomUser
from account.forms import CustomUserCreationForm, CustomUserChangeForm

# Define inline admin for Account model
class AccountInLine(admin.StackedInline):
    model = Account
    can_delete = False
    verbose_name_plural = 'Accounts'

# Customize admin for CustomUser model
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ["username", "email", "is_staff", "is_superuser"]
    inlines = [AccountInLine]  # Include inline Account admin

# Register the custom admin for CustomUser model
admin.site.register(CustomUser, CustomUserAdmin)