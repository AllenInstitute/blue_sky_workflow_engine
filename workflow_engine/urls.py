from django.conf.urls import url

from workflow_engine.views import delete_view
from workflow_engine.views import executable_view
from workflow_engine.views import job_queue_view
from workflow_engine.views import job_view
from workflow_engine.views import log_view
from workflow_engine.views import manual_queue_view
from workflow_engine.views import record_info_view
from workflow_engine.views import task_view
from workflow_engine.views import update_view
from workflow_engine.views import workflow_view
from workflow_engine.views import home_view

urlpatterns = [
    url(r'^$', home_view.index, name='index'),

    #jobs
    url(r'^jobs$', job_view.jobs, name='jobs'),
    url(r'^jobs/([0-9]+)/$', job_view.jobs_page, name='jobs'),
    url(r'^jobs/queue_job/$', job_view.queue_job, name='jobs'),
    url(r'^jobs/kill_job/$', job_view.kill_job, name='jobs'),
    url(r'^jobs/get_status/$', job_view.get_job_status, name='jobs'),
    url(r'^jobs/get_show_data/$', job_view.get_job_show_data, name='jobs'),
    url(r'^jobs/run_all/$', job_view.run_all_jobs, name='jobs'),

    #tasks
    url(r'^tasks$', task_view.tasks, name='tasks'),
    url(r'^tasks/([0-9]+)/$', task_view.tasks_page, name='tasks'),
    url(r'^tasks/get_show_data/$', task_view.get_tasks_show_data, name='tasks'),
    url(r'^tasks/queue_task/$', task_view.queue_task, name='tasks'),
    url(r'^tasks/kill_task/$', task_view.kill_task, name='tasks'),
    url(r'^tasks/get_status/$', task_view.get_task_status, name='tasks'),
    url(r'^tasks/download_bash/$', task_view.download_bash, name='tasks'),
    
    #workflows
    url(r'^workflows$', workflow_view.workflows, name='workflows'),
    url(r'^workflow_creator$', workflow_view.workflow_creator, name='workflow_creator'),
    url(r'^workflows/update_pbs$', workflow_view.update_pbs, name='workflows'),
    url(r'^workflows/get_head_workflow_node_id$', workflow_view.get_head_workflow_node_id, name='workflows'),
    url(r'^workflows/get_enqueued_objects$', workflow_view.get_enqueued_objects, name='workflows'),
    url(r'^workflows/create_job$', workflow_view.create_job, name='workflows'),
    url(r'^workflows/get_node_info$', workflow_view.get_node_info, name='workflows'),
    url(r'^workflows/update_workflow_node$', workflow_view.update_workflow_node, name='workflows'),
    url(r'^workflows/get_workflow_info$', workflow_view.get_workflow_info, name='workflows'),
    url(r'^workflows/update_workflow$', workflow_view.update_workflow, name='workflows'),
    url(r'^workflows/get_workflow_status$', workflow_view.get_workflow_status, name='workflows'),
    
    #job_queues
    url(r'^job_queues/get_show_data/$', job_queue_view.get_job_queues_show_data, name='job_queues'),
    url(r'^job_queues$', job_queue_view.job_queues, name='job_queues'),
    url(r'^job_queues/([0-9]+)/$', job_queue_view.job_queues_page, name='job_queues'),
    url(r'^job_queues/get_enqueued_object_classses$', job_queue_view.get_enqueued_object_classses, name='job_queues'),

    #executable
    url(r'^executables/([0-9]+)/$', executable_view.executables_page, name='executables'),
    url(r'^executables$', executable_view.executables, name='executables'),
    url(r'^executables/get_names$', executable_view.get_executable_names, name='executables'),

    #logs
    url(r'^logs/$', log_view.logs, name='logs'),

    #delete
    url(r'^delete_record/$', delete_view.delete_record, name='delete'),

    #update
    url(r'^update_record/$', update_view.update_record, name='update'),

    #record info
    url(r'^get_record_info/$', record_info_view.get_record_info, name='info'),
    url(r'^check_unique/$', record_info_view.check_unique, name='info'),
    url(r'^get_search_data/$', record_info_view.get_search_data, name='info'),

    #manual queues
    url(r'^manual_queues/check_if_finished/$', manual_queue_view.check_if_finished, name='manual_queues'),
]