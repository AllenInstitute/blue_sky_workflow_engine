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
## Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2019. Allen Institute. All rights reserved.
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
from django.db.models import Count
import pandas as pd
import simplejson as json
from django_pandas.io import read_frame
from workflow_engine.models import (
    WorkflowNode,
    WorkflowEdge,
    RunState
)

class WorkflowStatus(object):
    def __init__(self, workflow_names):
        self.workflow_names = workflow_names
        self.run_states = self.query_run_states()
        self.nodes, self.batch_size = self.query_nodes()
        self.edges = self.query_edges()
        self.run_state_counts = self.query_run_state_counts()
        self.reindex_run_state_counts()
        self.pending_queued_running = self.sum_pending_queued_running()
        self.run_state_totals = self.total_run_states()

    def query_run_states(self):
        run_states = read_frame(
            RunState.objects.values('id', 'name')
        )
        run_states.set_index(['id'], inplace=True)
        run_states.columns = ['run_state_name']

        return run_states

    def query_nodes(self):
        nodes = read_frame(
            WorkflowNode.safe_objects.values(
                'id',
                'job_queue__name',
                'batch_size'
            ).filter(
                workflow__name__in=self.workflow_names
            )
        )
        nodes.set_index(
            ['id'],
            inplace=True
        )
        nodes.columns = ['job_queue_name', 'batch_size']

        return nodes.loc[:,['job_queue_name']], nodes.loc[:,['batch_size']]

    def query_edges(self):
        edges = read_frame(
            WorkflowEdge.objects.values(
                'source__id', 'sink__id'
            ).filter(
                workflow__name__in=self.workflow_names
            )
        )
        edges.columns = ['source', 'target']
        edges.fillna(-1, inplace=True)
        edges.source = edges.source.astype(int)
        edges.target = edges.target.astype(int)
        edges.set_index(['source'], inplace=True)

        return edges

    def query_run_state_counts(self):
        qs = WorkflowNode.safe_objects.filter(
            workflow__name__in=self.workflow_names,
        ).values(
            'id',
            'job__run_state__id' # 'job_queue__name' for human-readable
        ).order_by(
            'id',
            'job__run_state__id', # 'job__run_state__name' for human-readable
        ).annotate(
            count=Count('job__run_state_id')
        ).all()

        run_state_counts = read_frame(qs)
        run_state_counts.columns=['job_queue', 'run_state', 'count']
        run_state_counts.set_index(['job_queue', 'run_state'], inplace=True)

        return run_state_counts

    def pending_queued_running_index(self, df):
        return df[df.run_state_name.isin(
            ['PENDING', 'QUEUED', 'RUNNING']
        )].index
    
    def sum_pending_queued_running(self):
        idx = pd.IndexSlice
        pqr_idx = self.pending_queued_running_index(self.run_states)
        df = self.run_state_counts.loc[idx[:,pqr_idx],:].sum(
            level='job_queue'
        )
        df.columns = ['pending_queued_running']
    
        return df

    def reindex_run_state_counts(self, verbose=False):
        if verbose:
            node_names = list(self.nodes['job_queue_name'])
            run_state_names = list(self.run_states['run_state_name'])
        else:
            node_names = list(self.nodes.index)
            run_state_names = list(self.run_states.index)
    
        idx = pd.MultiIndex.from_product(
            (node_names,run_state_names),
            names=['job_queue', 'run_state']
        )

        self.run_state_counts = self.run_state_counts.reindex(idx, fill_value=0)

    def total_run_states(self):
        totals = self.run_state_counts.sum(level='job_queue')
        totals.columns = [ 'total' ]

        return totals

    def status_as_dict(self):
        out_dict = {
            'edges': self.edges.groupby(
                self.edges.index
            )['target'].apply(list).to_dict()
        }
        out_dict.update(
            self.run_states.to_dict(orient='dict')
        )
        out_dict.update(
            self.nodes.to_dict(orient='dict')
        )
        out_dict.update(
            self.batch_size.to_dict(orient='dict')
        )
        out_dict.update(
            self.edges.groupby(
                self.edges.index
            )['target'].apply(list).to_dict()
        )
        out_dict.update(
            self.run_state_counts.to_dict(orient='dict')
        )
        out_dict.update(
            self.pending_queued_running.to_dict(orient='dict')
        )
        out_dict.update(
            self.run_state_totals.to_dict(orient='dict')
        )

        return out_dict

    def status_as_json(self):
        out_dict = {
            'edges':
                [ 
                    [ int(i), int(r.target) ]
                    for i,r in self.edges.iterrows()
                ]
        }
        out_dict.update(
            self.run_states.to_dict(orient='dict')
        )
        out_dict.update(
            self.nodes.to_dict(orient='dict')
        )
        out_dict.update(
            self.batch_size.to_dict(orient='dict')
        )
        out_dict.update(
            json.loads(self.run_state_counts.to_json(orient='columns'))
        )
        out_dict.update(
            self.pending_queued_running.to_dict(orient='dict')
        )
        out_dict.update(
            self.run_state_totals.to_dict(orient='dict')
        )

        return json.dumps(out_dict, indent=2)
