from django.contrib import admin


class WorkflowAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'description',
        'disabled',
        'use_pbs',
        ]
    list_select_related = []
    list_filter = []
    actions = []
    inlines = []
