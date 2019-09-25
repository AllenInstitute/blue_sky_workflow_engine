from django.contrib.contenttypes.models import ContentType
from workflow_engine.mixins import Enqueueable
from workflow_engine.models import (
    Job,
    JobQueue,
    Workflow,
    WorkflowNode
)
import pandas as pd
from django_pandas.io import read_frame
import itertools as it


class EnqueueableJobGrid(object):
    '''Queries for a subset of enqueued objects (rows), workflow nodes (columns)
    and Jobs (grid entries) with information to display a grid view of progress
    through the workflow. While this class may be used alone for simple workflows,
    a complex job grid with multiple enqueued object types should subclass it.

    See also the :class:`workflow_engine.views.faster_job_grid.FasterJobGrid`
    view for how to call it and the job_grid.js javascript client for rendering.

    Notes
    -----
    Dataframes representing partial calculations are saved as data members
    so they can be printed for debugging. This may change in the future.
    '''

    RUN_STATE_LETTERS = {
        "PENDING": "p",
        "QUEUED": 'q',
        "RUNNING": 'r',
        "FINISHED_EXECUTION": 'n',
        "SUCCESS": 's',
        "FAILED": 'f',
        "FAILED_EXECUTION": 'x',
        "PROCESS_KILLED": 'k',
    }
    '''single letter codes used to keep user interface and messages dense.
    '''

    SERIALIZE_COLUMNS = [
        'z_index',
        'object_state_id',
        'workflow_node',
        'letter_code',
        'job_id',
        'enqueued_object_type',
        'enqueued_object_id',
        'start',
        'end'
    ]
    '''ordered list of columns from the annotated job dataframe to send.
    '''

    def __init__(self, row_range, order=None):
        '''Set up data members to hold partial job grid calculation results.

        Parameters
        ----------
        order: list of strings
            Ordered list of job queue names
        '''
        self.model_classes = self.get_model_classes()
        self.model_types = self.get_model_types(self.model_classes) 
        self.row_range = row_range
        if order is None:
            self.order = self.get_node_order()
        else:
            self.order = order
        self.job_df = None
        self.node_id_order = None
        self.run_state_df = None
        self.enqueued_object_row_df = None
        self.annotated_enqueued_object_row_df = None
        self.grid_df = None
        self.annotated_job_df =None
        self.workflow_node_df = None

    def get_model_types(self, model_classes):
        '''Convert model classes to strings using the content type framework.
        '''
        self.model_types = [
            ContentType.objects.get_for_model(c).name.replace(' ', '')
            for c in model_classes
        ]

        return self.model_types

    def get_node_order(self):
        '''Override with a specific list of job queue names.
        These will be used in order as the columns of the job grid.

        Returns
        -------
        list of string
        '''
        return [j.name for j in JobQueue.objects.order_by('id')]


    def get_model_classes(self):
        '''Models to be queried for display in the grid.
        Override to provide a specific list of model classes.
        They must implement :class:`workflow_engine.mixins.enqueueable.Enqueueable`
 
        Returns
        -------
        list of Model
            model classes that implement Enqueueable

        Notes
        -----
        By default, immediate subclasses of Enqueueable 
        will be included, but not leaf descendant classes.
        '''
        return Enqueueable.__subclasses__() 

    def get_workflow_names(self):
        return [w.name for w in Workflow.objects.order_by('id')]

    def query_node_id_order(self):
        '''Get a list of workflow node ids corresponding to the grid columns

        Returns
        -------
        list of int
            workflow node ids

        Note
        ----
        Despite the name, the query in this method doesn't sort the nodes.
        '''
        workflow_names = self.get_workflow_names() 
        
        self.node_id_order = [
            n.id for n in it.chain.from_iterable(WorkflowNode.objects.filter(
                workflow__name__in=workflow_names,
                job_queue__name=job_queue_name
            ) for job_queue_name in self.order)
        ]

        return self.node_id_order

    def query_job_df(self):
        '''Initial query of job information.

        Returns
        -------
        DataFrame
            Jobs with generic enqueued object, run state and time information

        Notes
        -----
        Do not override.
        This dataframe will be combined with others.
        Final ordering will be done elsewhere using Pandas rather than the database.
        TODO: add a filter clause on the rows.
        '''
        self.job_df = read_frame(
            Job.objects.filter(
                enqueued_object_type__model__in=self.model_types,
            ).values(
                'id',
                'enqueued_object_type__model',
                'enqueued_object_id',
                'workflow_node__id',
                'running_state',
                'start_run_time',
                'end_run_time'
            ).order_by(# don't have to sort in the database if we do it in pandas
                'enqueued_object_id',
                'workflow_node_id',  # sort by order later
                'running_state'
            )
        )
        self.job_df.columns = [
            'job_id',
            'enqueued_object_type',
            'enqueued_object_id',
            'workflow_node',
            'run_state',
            'start',
            'end'
        ]

        return self.job_df

    def build_run_state_df(self):
        '''Helper dataframe to cross-reference run state name, index and lestters.

        Returns
        -------
        Dataframe

        Notes
        -----
        Do not override
        '''
        run_state_letters_df = pd.DataFrame.from_dict(
            EnqueueableJobGrid.RUN_STATE_LETTERS,
            orient='index'
        )
        run_state_letters_df.reset_index(level=0, inplace=True)
        run_state_letters_df.columns = ['run_state', 'letter_code']

        run_state_names_df = pd.DataFrame(
            list(enumerate(Job.get_run_state_names()))
        )
        run_state_names_df.columns = ['run_state_id', 'run_state']

        self.run_state_df = run_state_names_df.merge(
            run_state_letters_df,
            on='run_state'
        )

        return self.run_state_df

    def query_enqueued_object_row_df(self):
        '''Get the row objects for the job grid.

        Returns
        -------
        dataframe of enqueued object ids, types and row coordinate

        Notes
        -----
        Different enqueued object types may need to be mapped to a row differently.
        '''
        row_dfs = []

        for model_clz in self.get_model_classes():
            row_df = read_frame(
                model_clz.objects.values(
                    'id',
                    # TODO: figure out how to get the z_index here.
                    'object_state'
                ).filter(
                    id__gte=self.row_range[0],
                    id__lte=self.row_range[1]
                )
            )
            row_df.columns = [
                'enqueued_object_id',
                'object_state'
            ]
            row_df = row_df.assign(
                z_index=row_df['enqueued_object_id'], # TODO: need real row coord
                enqueued_object_type=ContentType.objects.get_for_model(
                    model_clz
                ).name.replace(' ', '')
            )
            row_dfs.append(row_df)

        self.enqueued_object_row_df = pd.concat(row_dfs)

        return self.enqueued_object_row_df

    def query_object_state_df(self):
        '''
        Notes
        -----
        Do not override.
        Not sure what will happen for models that do not mixin Stateful.
        '''
        self.object_state_df = pd.concat(
            [
                read_frame(
                    clz.objects.values(
                        'object_state',
                    ).distinct()
                )
                for clz in self.model_classes
            ]
        ).drop_duplicates().reset_index(drop=True)
        self.object_state_df.reset_index(level=0, inplace=True)
        self.object_state_df.columns = (['object_state_id', 'object_state'])

        return self.object_state_df

    def generate_grid_df(self):
        '''
        '''
        self.grid_df = self.annotated_enqueued_object_row_df.merge(
            self.job_df,
            on=['enqueued_object_type', 'enqueued_object_id'],
            how='left'
        ).merge(
            self.object_state_df,
            on='object_state',
            how='left'
        )

        return self.grid_df

    def annotate_enqueued_object_row_df(self):
        '''Override to add extra information about enqueued objects
        '''
        self.annotated_enqueued_object_row_df = self.enqueued_object_row_df

        return self.annotated_enqueued_object_row_df

    def annotate_job_df(self):
        self.annotated_job_df = self.grid_df.merge(
           self.run_state_df,
           on='run_state',
           how='left'
        )

        return self.annotated_job_df

    def query_workflow_node_df(self):
        '''Get a set of workflow nodes as a dataframe for the grid columns
        '''
        self.workflow_node_df = read_frame(
            WorkflowNode.objects.values(
                'id',
                'job_queue__name'
            ).filter(
                id__in=self.node_id_order,
            )
        )
        self.workflow_node_df.columns = [
            'workflow_node_id', 'workflow_node'
        ]

        return self.workflow_node_df

    def build_serializable_dict(self):
        '''Build up the partial dataframes into a sorted and annotated dataframe that is
        easy to serialize and render by a javascript client.
        '''
        self.query_node_id_order()
        self.query_job_df()
        self.build_run_state_df()
        self.query_enqueued_object_row_df()
        self.annotate_enqueued_object_row_df()
        self.query_object_state_df()
        self.generate_grid_df()
        annotated_job_df = self.annotate_job_df()
        self.query_workflow_node_df()

        serial_df = annotated_job_df[
            EnqueueableJobGrid.SERIALIZE_COLUMNS
        ].fillna(value=-1)
        serial_df = serial_df[
            (serial_df.z_index >= self.row_range[0]) & 
            (serial_df.z_index <= self.row_range[1])
        ]

        return serial_df

    def serialize_grid_dict(self, serial_dataframe):
        '''Create json with data needed serialize and display a job grid.
        '''
        serial_json = serial_dataframe.to_dict(orient='split')
        del serial_json['index']

        payload = serial_json

        payload['run_states_by_id'] = self.run_state_df.set_index(
            'run_state_id'
        ).fillna(value=-1).to_dict(orient='index')

        payload['run_states_by_letter'] = self.run_state_df.set_index(
            'letter_code'
        ).fillna(value=-1).to_dict(orient='index')

        payload.update(
            self.workflow_node_df.set_index(
                'workflow_node_id'
            ).fillna(value=-1).to_dict()
        )

        payload['node_order'] = self.node_id_order

        payload.update(
            self.object_state_df.set_index(
                'object_state_id'
            ).to_dict()
        )

        return payload

    def get_dict(self):
        serial_df = self.build_serializable_dict()

        # return self.serialize_grid_dict(serial_df)
        serial_json = serial_df.to_dict(orient='split')
        del serial_json['index']

        payload = serial_json
        payload['run_states_by_id'] = self.run_state_df.set_index('run_state_id').fillna(value=-1).to_dict(orient='index')
        payload['run_states_by_letter'] = self.run_state_df.set_index('letter_code').fillna(value=-1).to_dict(orient='index')
        payload.update(
            self.workflow_node_df.set_index('workflow_node_id').fillna(value=-1).to_dict())
        payload['node_order'] = self.node_id_order
        payload.update(
            self.object_state_df.set_index('object_state_id').to_dict())

        return payload
