from django.contrib import admin


class JobQueueAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'job_strategy_class',
        'enqueued_object_class',
        ]
    list_select_related = []
    list_filter = []
    actions = []
    inlines = []
