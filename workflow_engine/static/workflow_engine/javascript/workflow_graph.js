
function draw_workflow1(workflow_nodes, workflow_edges) {
    alert(workflow_nodes);
}


var state_hash = {}

function node_number_string(n) {
    try {
        s = '(' + state_hash[n]['TOTAL'] + ') ' + 
            (state_hash[n]['PENDING'] + 
            state_hash[n]['QUEUED'] + 
            state_hash[n]['RUNNING']) + ' / ' +
            ' ' + state_hash[n]['BATCH_SIZE'];
    } catch(e) {
        s = e;
    }

    return s;
}


function node_color(n) {
    if (!(n in state_hash)) {
        return 'grey';
    }

    try {
        if ((state_hash[n]['FAILED'] > 0) ||
            (state_hash[n]['FAILED_EXECUTION']) > 0){
            return 'red';
        } else if (
            (state_hash[n]['RUNNING'] > 0) ||
            (state_hash[n]['PENDING'] > 0) ||
            (state_hash[n]['QUEUED'] > 0)) {
            return 'green';
        } else if (
            (state_hash[n]['FAILED'] > 0)) {
            return 'blue';
        } else {
            return 'blue';
        }
    } catch(err) {
        return 'grey';
    }
}

function color_nodes(run_states) {
    state_hash = {};

    for (i in run_states) {
        job_queue_name = run_states[i]['node'];

        state_hash[job_queue_name] = {
            'TOTAL': 0
        }

        if (run_states[i]['state'] == 'BATCH_SIZE') {
            state_hash[job_queue_name]['BATCH_SIZE'] = run_states[i]['count']
        }
    }

    for (i in run_states) {
        job_queue_name = run_states[i]['node'];
        state_name = run_states[i]['state']
        if (state_name != 'BATCH_SIZE') {
            queue_state_count = run_states[i]['count']
            queue_entry = state_hash[job_queue_name]
            queue_entry[state_name] = queue_state_count;
            queue_entry['TOTAL'] = queue_entry['TOTAL'] + queue_state_count;
        }
    }

    var cy_nodes = window.cy.nodes()

    for (i = 0; i < cy_nodes.length; i++) {
        job_queue_name = cy_nodes[i].data()['id'];
        state_color = node_color(job_queue_name);
        cy_nodes[i].classes(state_color + 'Class');
        cy_nodes[i].data(
            'label',
            job_queue_name.replace(
                / /g, '\n') + '\n' + node_number_string(job_queue_name))
    }
}

function draw_workflow(workflow_nodes, workflow_edges) {
var cy = window.cy = cytoscape({
  container: document.getElementById('cy'),

  boxSelectionEnabled: false,
  autounselectify: true,

  layout: {
    name: 'dagre',
    fit: false,
    spacingFactor: 0.75
  },

  style: [
    {
      selector: 'node',
      style: {
        'shape': 'roundrectangle',
        'content': 'data(label)',
        'font-size': '10px',
        'font-weight': 'bold',
        'text-opacity': 0.6,
        'text-valign': 'center',
        'text-halign': 'center',
        'text-wrap': 'wrap',
        //'text-max-width': 50,
        'width': 60,
        'height': 60,
      }
    },

    {
      selector: 'edge',
      style: {
        'curve-style': 'bezier',
        'width': 4,
        'target-arrow-shape': 'triangle',
        'line-color': 'steelblue',
        'opacity': 0.3,
        'target-arrow-color': 'steelblue'
      }
    },

    {
        selector: '.redClass',
        style: {
        'background-color': 'lightcoral',
        'shape': 'rectangle'
       }
    },
    {
        selector: '.greenClass',
        style: {
        'background-color': 'lightgreen',
        'shape': 'rectangle'
       }
    },
    {
        selector: '.blueClass',
        style: {
        'background-color': 'lightblue',
        'shape': 'rectangle'
       }
    },
    {
        selector: '.greyClass',
        style: {
        'background-color': 'lightgrey',
        'shape': 'rectangle'
       }
    }
    ],

  elements: {
    nodes: workflow_nodes.map(
        n => {
            return {
                data: {
                    id: n,
                    label: n
                },
                classes: 'multiline-manual'
            } }),
    edges: workflow_edges.map(
        e => {
            return { data: e } }),
  },
});
}


function render_workflow_graph() {
    graph_url = '/static/workflow_engine/javascript/monitor_out.js';

    fetch(graph_url, {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
    .then((response) => {
        response.json().then(obj => {
            draw_workflow(obj['nodes'], obj['edges']);
            color_nodes(obj['run_states']);
        })
    })
}


var $ = django.jQuery;
$(document).ready(function(){
    render_workflow_graph();
    setInterval(render_workflow_graph, 60*1000);
})
