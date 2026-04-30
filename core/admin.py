from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Page, Campaign, Person, TrackedLink, ClickLog

@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ('name', 'target_url')
    search_fields = ('name', 'target_url')

@admin.register(Campaign)
class CampaignAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Person)
class PersonAdmin(ModelAdmin):
    list_display = ('name', 'email_or_whatsapp')
    search_fields = ('name', 'email_or_whatsapp')

@admin.register(TrackedLink)
class TrackedLinkAdmin(ModelAdmin):
    list_display = ('shortcode', 'page', 'campaign', 'person', 'created_at')
    list_filter = ('campaign', 'page', 'person')
    search_fields = ('shortcode', 'person__name', 'campaign__name', 'page__name')
    readonly_fields = ('shortcode', 'created_at')

@admin.register(ClickLog)
class ClickLogAdmin(ModelAdmin):
    list_display = ('tracked_link', 'ip_address', 'timestamp')
    list_filter = ('tracked_link__campaign', 'timestamp')
    search_fields = ('tracked_link__shortcode', 'ip_address')
    readonly_fields = ('tracked_link', 'ip_address', 'user_agent', 'timestamp')
    
    def has_add_permission(self, request):
        return False

from .models import Invite
from django.utils.html import format_html

@admin.register(Invite)
class InviteAdmin(ModelAdmin):
    list_display = ('code', 'is_used', 'created_at', 'get_invite_link')
    list_filter = ('is_used',)
    search_fields = ('code',)
    
    def get_invite_link(self, obj):
        # Gera o link para o admin copiar facilmente
        url = f"/register/?code={obj.code}"
        return format_html(f'<a href="{url}" target="_blank">{url}</a>')
    get_invite_link.short_description = "Link para enviar ao funcionário"
