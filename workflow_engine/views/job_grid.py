import django; django.setup()
import pandas as pd
from workflow_engine.models.workflow_node import WorkflowNode
from workflow_engine.models.job import Job
from workflow_engine.models.job_queue import JobQueue
from django_pandas.io import read_frame
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
        self.workflow_node_df.loc[:,'parent'] = \
            [str(wn) for wn in self.workflow_nodes]
        self.workflow_node_df.loc[:,'parent_id'] = \
            [wn.parent.pk if wn.parent else None for wn in self.workflow_nodes]

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
                            self.workflow_node_df.parent_id == float(current_node)].id)
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
            how='left')#.dropna(subset=['end_run_time'])

        enqueued_object_job_df = enqueued_object_job_df.sort_values(
            by=[self.index_field(), 'end_run_time'],
            axis='rows',
            ascending=[True, True],
            na_position='first')

        enqueued_object_job_df.loc[:,'job_and_state'] = \
            enqueued_object_job_df.loc[:,['job_id','run_state','enqueued_object_id']].apply(
                lambda x: '{}/{}/{}'.format(*x),
                axis=1)

        grid_df = pd.pivot_table(
            enqueued_object_job_df,
            values='job_and_state',
            index=self.index_field(),
            columns=['workflow_node'],
            aggfunc='last')

        sorted_node_names = list(self.filter_workflow_nodes().job_queue)
        grid_df = grid_df[sorted_node_names]

        grid_df.loc[-1,:] = grid_df.count()

        extra_columns = [ self.index_field() ]
        extra_columns.extend(self.extra_columns())

        return grid_df.merge(
            self.enqueued_object_df.loc[:,extra_columns],
            left_index=True,
            right_on=self.index_field(),
            how='left').set_index(self.index_field())


    def filter_workflow_nodes(self):
        return self.sorted_nodes_df

    def query_enqueued_objects(self):
        pass

    def extra_columns(self):
        return []

    def index_field(self):
        return 'index'  # TODO: default? or raise abstract class exception
