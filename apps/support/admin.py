from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'email', 'first_name', 'last_name', 'created_at', 'is_resolved')
    list_filter = ('subject', 'is_resolved', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'message')
    readonly_fields = ('created_at',)
