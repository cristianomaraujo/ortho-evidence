import unittest,copy,json
from test_extraction import m,ROOT
class VersionTwo(unittest.TestCase):
 def setUp(self):
  self.schema=json.loads((ROOT/'extraction/schema-v2.json').read_text());self.record={'title':'A chapter','abstract':'14 records were selected for qualitative analysis. Search ended June 23, 2026.'};self.r={k:{'status':'not_reported','value':None,'evidence':[]} for k in m.FIELDS};self.r['comparator']['kind']='not_reported';self.r.update({'review_types':{'values':['not_reported'],'evidence':[]},'included_counts':{'status':'not_reported','items':[]},'document_kind':{'value':'chapter','evidence':[{'source':'title','quote':'chapter'}]},'search_end_dates':[],'warnings':[]})
 def test_record_unit_preserved(self):
  self.r['included_counts']={'status':'reported','items':[{'number':14,'unit':'records','scope':'whole_review','evidence':{'source':'abstract','quote':'14 records were selected for qualitative analysis.'}}]};m.validate(self.r,self.record,self.schema);self.assertEqual(self.r['included_counts']['items'][0]['unit'],'records')
 def test_date_uses_execution_date(self):
  self.r['search_end_dates']=[{'date_iso':'2026-06-23','evidence':{'source':'abstract','quote':'June 23, 2026'}}];m.validate(self.r,self.record,self.schema);self.assertFalse(m.date_checks(self.r,'2026-10-09')[0]['is_future']);self.assertTrue(m.date_checks(self.r,'2026-06-01')[0]['is_future'])
 def test_comparator_kind_consistent(self):
  self.r['comparator']['kind']='planned_vs_achieved'
  with self.assertRaises(ValueError):m.validate(self.r,self.record,self.schema)
 def test_invalid_calendar_date_rejected(self):
  self.r['search_end_dates']=[{'date_iso':'2026-02-30','evidence':{'source':'abstract','quote':'June 23, 2026'}}]
  with self.assertRaises(ValueError):m.validate(self.r,self.record,self.schema)
