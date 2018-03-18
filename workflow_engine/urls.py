# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Redistributions for commercial purposes are not permitted without the
# Allen Institute's written permission.
# For purposes of this license, commercial purposes is the incorporation of the
# Allen Institute's software into anything for which you will charge fees or
# other compensation. Contact terms@alleninstitute.org for commercial licensing
# opportunities.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
from django.conf.urls import url

from workflow_engine.views import executable_view
from workflow_engine.views import job_queue_view
from workflow_engine.views import job_view
from workflow_engine.views import log_view
from workflow_engine.views import manual_queue_view
from workflow_engine.views import record_view
from workflow_engine.views import task_view
from workflow_engine.views import workflow_view
from workflow_engine.views import home_view
from workflow_engine.views.monitor_view import MonitorView

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
    url(r'^workflows/run_jobs$', workflow_view.run_jobs, name='workflows'),
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

    #record info, update, delete
    url(r'^delete_record/$', record_view.delete_record, name='delete'),
    url(r'^update_record/$', record_view.update_record, name='update'),
    url(r'^get_record_info/$', record_view.get_record_info, name='info'),
    url(r'^check_unique/$', record_view.check_unique, name='info'),
    url(r'^get_search_data/$', record_view.get_search_data, name='info'),

    #manual queues
    url(r'^manual_queues/check_if_finished/$', manual_queue_view.check_if_finished, name='manual_queues'),

   url(r'^data', MonitorView.as_view())
]