from django.contrib import admin


class WellKnownFileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'attachable_type',
        'attachable_id',
        'record_dir',
        'record_filename',
        'well_known_file_type',
        'created_at',
        'updated_at'
        )
    read_only_fields = (
        'record_dir',
        'record_filename',
        'created_at',
        'updated_at'
        )
    list_select_related = []
    list_filter = [
        'attachable_type',
        'well_known_file_type'
    ]

    def record_dir(self, wkf_object):
        return wkf_object.get_most_recent_file_record().storage_directory

    def record_filename(self, wkf_object):
        return wkf_object.get_most_recent_file_record().filename






