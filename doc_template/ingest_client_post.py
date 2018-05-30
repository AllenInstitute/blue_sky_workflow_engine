import requests

url = 'http://ibs-timf-ux1:9002/workflow_engine/ingest/'
workflow = 'em_2d_montage'

body = {
    "this": "is",
    "a": "test"
}

r = requests.post(url=url+workflow, json=body)

print(r.json())
