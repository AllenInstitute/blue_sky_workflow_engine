
function draw_workflow1(workflow_nodes, workflow_edges) {
    alert(workflow_nodes);
}

function draw_workflow(workflow_nodes, workflow_edges) {
var cy = window.cy = cytoscape({
  container: document.getElementById('cy'),

  boxSelectionEnabled: false,
  autounselectify: true,

  layout: {
    name: 'dagre',
    fit: false,
  },

  style: [
    {
      selector: 'node',
      style: {
        'content': 'data(id)',
        'font-size': '24px',
        'text-opacity': 0.6,
        'text-valign': 'center',
        'text-halign': 'right',
        'background-color': 'lightblue'
      }
    },

    {
      selector: 'edge',
      style: {
        'curve-style': 'bezier',
        'width': 4,
        'target-arrow-shape': 'triangle',
        'line-color': 'steelblue',
        'target-arrow-color': 'steelblue'
      }
    }
  ],

  elements: {
    nodes: workflow_nodes.map(n => { return { data: {id: n} } }),
    edges: workflow_edges.map(e => { return { data: e } }),
  },
});
}


var $ = django.jQuery;
$(document).ready(function(){
    fetch('/workflow_engine/workflows/monitor', {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
    .then((response) => {
        response.json().then(obj => {
            draw_workflow(obj['nodes'], obj['edges'])
        })
    })
})
