import unittest,importlib.util,copy,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('extract',ROOT/'scripts/extract_reviews.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ExtractionChecks(unittest.TestCase):
 def setUp(self):
  self.schema=json.loads((ROOT/'extraction/schema-v1.json').read_text());self.record={'title':'A scoping review of aligners','abstract':'We assessed pain in adults. Twelve studies were included.'}
  self.result={k:{'status':'not_reported','value':None,'evidence':[]} for k in m.FIELDS};self.result.update({'review_types':{'values':['scoping_review'],'evidence':[{'source':'title','quote':'scoping review'}]},'included_counts':{'status':'not_reported','items':[]},'warnings':[]})
 def test_missing_is_not_zero(self):
  m.validate(self.result,self.record,self.schema);self.assertEqual(self.result['included_counts']['items'],[])
 def test_fabricated_evidence_rejected(self):
  r=copy.deepcopy(self.result);r['objective']={'status':'reported','value':'Assess pain','evidence':[{'source':'abstract','quote':'We assessed pain in children.'}]}
  with self.assertRaises(ValueError):m.validate(r,self.record,self.schema)
 def test_reported_without_support_rejected(self):
  r=copy.deepcopy(self.result);r['population']={'status':'reported','value':'Adults','evidence':[]}
  with self.assertRaises(ValueError):m.validate(r,self.record,self.schema)
 def test_cache_invalidates_when_insights_change(self):
  config={'model':'model-snapshot','max_output_tokens':4096};key=m.cache_key(self.record,config,'prompt',self.schema)
  for rec,cfg,prompt,schema in [({**self.record,'abstract':'changed'},config,'prompt',self.schema),(self.record,{**config,'model':'other'},'prompt',self.schema),(self.record,config,'new prompt',self.schema),(self.record,config,'prompt',{**self.schema,'description':'changed'})]:self.assertNotEqual(key,m.cache_key(rec,cfg,prompt,schema))
 def test_incomplete_and_refused_not_cached(self):
  for raw in [{'status':'incomplete','output':[]},{'status':'completed','output':[{'content':[{'type':'refusal'}]}]}]:
   with self.assertRaises(ValueError):m.parse_response(raw)
 def test_no_abstract_generates_no_planned_request(self):
  config={'expected_output_tokens':1200,'max_output_tokens':4096};est=m.estimate([{'title':'Title','abstract':''}],config,'prompt',self.schema);self.assertEqual(est['eligible_requests'],0);self.assertEqual(est['expected_usd'],None)
 def test_count_unit_and_subset_retained(self):
  r=copy.deepcopy(self.result);r['included_counts']={'status':'reported','items':[{'number':12,'unit':'studies','scope':'whole_review','evidence':{'source':'abstract','quote':'Twelve studies were included.'}}]};m.validate(r,self.record,self.schema);self.assertEqual(r['included_counts']['items'][0]['number'],12)
 def test_unknown_output_fields_rejected(self):
  r=copy.deepcopy(self.result);r['saturation']='high'
  with self.assertRaises(ValueError):m.validate(r,self.record,self.schema)
if __name__=='__main__':unittest.main()
