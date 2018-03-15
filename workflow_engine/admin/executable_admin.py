from django.contrib import admin


class ExecutableAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'description',
        'executable_path',
        'pbs_executable_path',
        'static_arguments',
        'pbs_queue',
        'pbs_processor',
        'pbs_walltime',
        'created_at',
        'updated_at'
        ]
    list_select_related = []
    list_filter = []
    actions = []
    inlines = []
