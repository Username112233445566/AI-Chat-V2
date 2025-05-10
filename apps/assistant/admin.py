from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import (
    AssistantUser,
    TelegramGroup,
    YouGileBoard,
    AssistantKeywords,
    AssistantPromt,
    Secret
)

admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(AssistantUser)
class AssistantUserAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'tg_id', 'can_submit_tasks',
        'is_active', 'first_seen_at', 'last_message_at'
    )
    list_filter = ('can_submit_tasks', 'is_active', 'telegram_groups', 'yougile_boards')
    search_fields = ('full_name', 'tg_id')
    filter_horizontal = ('telegram_groups', 'yougile_boards')
    readonly_fields = ('first_seen_at', 'last_message_at')
    ordering = ('-last_message_at',)


@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'chat_id', 'is_active', 'updated_at')
    search_fields = ('name', 'chat_id')
    list_filter = ('is_active', 'updated_at')


@admin.register(YouGileBoard)
class YouGileBoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'board_id', 'column_id', 'is_active', 'updated_at')
    search_fields = ('name', 'board_id', 'column_id')
    list_filter = ('is_active', 'updated_at')


@admin.register(AssistantKeywords)
class AssistantKeywordsAdmin(admin.ModelAdmin):
    list_display = ('keywords', 'is_active', 'updated_at')
    search_fields = ('keywords',)
    list_filter = ('is_active', 'updated_at')


@admin.register(AssistantPromt)
class AssistantPromtAdmin(admin.ModelAdmin):
    list_display = ('short_prompt', 'is_active', 'updated_at')
    list_filter = ('is_active', 'updated_at')

    def short_prompt(self, obj):
        return obj.prompt[:75] + ("..." if len(obj.prompt) > 75 else "")
    short_prompt.short_description = "Промт"


@admin.register(Secret)
class SecretAdmin(admin.ModelAdmin):
    list_display = ('short_bot_token', 'short_ai_key', 'short_group_id', 'updated_at')

    def short_bot_token(self, obj):
        return obj.value_bot[:12] + "..."

    def short_ai_key(self, obj):
        return obj.value_ai[:12] + "..."

    def short_group_id(self, obj):
        return obj.value_group[:12] + "..."

    short_bot_token.short_description = "Bot Token"
    short_ai_key.short_description = "AI Key"
    short_group_id.short_description = "Group ID"