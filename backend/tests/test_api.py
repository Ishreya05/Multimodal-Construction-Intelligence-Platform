from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
def test_health():
    r=client.get('/health'); assert r.status_code==200 and r.json()['status']=='ok'
def test_estimate():
    r=client.post('/api/estimate',json={'project_type':'Residential','area_sqft':1000,'floors':1,'location':'Indore','quality':'standard','notes':''})
    assert r.status_code==200 and r.json()['total']>0 and len(r.json()['items'])>=4
def test_schedule():
    r=client.post('/api/schedule',json={'project_type':'Residential','area_sqft':1000,'floors':1,'location':'India','quality':'standard','notes':''})
    assert r.status_code==200 and r.json()['total_duration_days']>0
def test_valuation():
    r=client.post('/api/valuation',json={'area_sqft':1000,'location':'Indore','rate_per_sqft':2500})
    assert r.status_code==200 and r.json()['estimated_value']==2500000
def test_design_brief():
    r=client.post('/api/design-brief',json={'area_sqft':1200,'style':'Contemporary'})
    assert r.status_code==200 and 'visualization_prompt' in r.json()
def test_invalid_area_rejected():
    r=client.post('/api/estimate',json={'area_sqft':-1})
    assert r.status_code==422
