import django; django.setup()
import pandas as pd
from workflow_engine.models import (
    WorkflowNode,
    Job,
    JobQueue
)
from django_pandas.io import read_frame
import numpy as np
from collections import deque
import itertools as it


class JobGrid(object):
    def __init__(self):
        self.workflow_nodes = None
        self.workflow_node_df = None
        self.job_queues = None
        self.job_queue_df = None
        self.workflow_node_df = None
        self.jobs = None
        self.jobs_df = None
        self.em_mset_job_df = None
        self.enqueued_objects = None
        self.enqueued_object_df = None

    def query_workflow_objects(self):
        self.workflow_nodes = WorkflowNode.objects.filter(archived=False)
        self.workflow_node_df = read_frame(self.workflow_nodes)
        self.workflow_node_df.loc[:,'parent'] = [
            str(wn.sources.first())
            if wn.sources.count() >= 1 else None
            for wn in self.workflow_nodes
        ]
        self.workflow_node_df.loc[:,'parent_id'] = [
            wn.sources.first().pk
            if wn.sources.count() >= 1 else None
            for wn in self.workflow_nodes
        ]
        self.job_queues = JobQueue.objects.filter(archived=False)
        self.job_queue_df = read_frame(self.job_queues)

        self.job_queue_df.loc[:,'enqueued_object_type'] = \
            [str(jq.enqueued_object_type) for jq in self.job_queues]

        self.workflow_node_df = self.workflow_node_df.merge(
            self.job_queue_df.loc[:,['name', 'enqueued_object_type']],
            left_on='job_queue',
            right_on='name').drop('name', axis='columns')

        self.sort_workflow_nodes()

        self.jobs = Job.objects.filter(
            workflow_node_id__in=list(self.filter_workflow_nodes().id),
            archived=False)
        self.job_df = read_frame(self.jobs, index_col='id')
        self.job_df.loc[:,'job_id'] = self.job_df.index

    def sort_workflow_nodes(self):
        workflow_list = []
 
        head_nodes = list(
            self.workflow_node_df[
                self.workflow_node_df.is_head==True].id)
        head_nodes.sort()
        for h in head_nodes:
            working_list = deque((h,))
            node_list = [h]

            try:
                while True:
                    current_node = working_list.popleft()
                
                    if current_node in working_list:
                        continue

                    children = list(
                        self.workflow_node_df[
                            self.workflow_node_df.parent_id == \
                                float(current_node)].id)
                    children.sort()

                    for c in children:
                        if not c in node_list:
                            node_list.append(c)
                            working_list.append(c)
            except:
                pass
            finally:
                workflow_list.append(node_list)
            
        node_ids = list(it.chain(*workflow_list))

        self.sorted_nodes_df = pd.DataFrame(
            node_ids, columns=['id']).merge(
                self.workflow_node_df)

    def generate_grid(self):
        enqueued_object_job_df = self.job_df.merge(
            self.enqueued_object_df,
            left_on='enqueued_object_id',
            right_index=True,
            how='left')

        sort_cols = self.sort_columns()
        sort_cols.append('end_run_time')

        enqueued_object_job_df = \
            enqueued_object_job_df.sort_values(
                by=sort_cols,
                axis='rows',
                na_position='first')

        enqueued_object_job_df.loc[:,'job_and_state'] = \
            enqueued_object_job_df.loc[:, [
                'job_id','run_state','enqueued_object_id'
            ]].apply(
                lambda x: '{}/{}/{}'.format(*x),
                axis=1)

        grid_df = pd.pivot_table(
            enqueued_object_job_df,
            values='job_and_state',
            index=self.index_field(),
            columns=['workflow_node'],
            aggfunc='last')

        for n in self.sorted_node_names():
            if n not in grid_df.columns:
                grid_df[n] = np.NaN

        grid_df = grid_df[self.sorted_node_names()]

        grid_df.loc[-1,:] = grid_df.count()

        grid_df = grid_df.merge(
            self.enqueued_object_df.loc[:,self.extra_columns()],
            left_index=True,
            right_on='id',
            how='outer')

        return grid_df.sort_values(
            by=self.sort_columns(),
            axis='rows')

    def sorted_node_names(self):
        return list(self.filter_workflow_nodes().job_queue)

    def filter_workflow_nodes(self):
        return self.sorted_nodes_df

    def query_enqueued_objects(self):
        pass

    def extra_columns(self):
        return []

    def index_field(self):
        return 'enqueued_object_id'

    def sort_columns(self):
        return [ self.index_field() ]
