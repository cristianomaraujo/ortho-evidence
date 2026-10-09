#!/usr/bin/env python3
"""Offline, reproducible operational pilot and schema preparation. No API calls."""
import json,random,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def obj(props):return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}
string={'type':'string'}
evidence=obj({'source':{'type':'string','enum':['title','abstract']},'quote':string})
field=obj({'status':{'type':'string','enum':['reported','not_reported','unclear']},'value':{'type':['string','null']},'evidence':{'type':'array','items':evidence}})
count=obj({'number':{'type':'integer'},'unit':{'type':'string','enum':['studies','articles','trials','publications']},'scope':{'type':'string','enum':['whole_review','subset','unclear']},'evidence':evidence})
schema=obj({**{k:field for k in ['objective','population','intervention_or_exposure','comparator','outcomes','context']},'review_types':obj({'values':{'type':'array','items':{'type':'string','enum':['systematic_review','meta_analysis','scoping_review','mapping_review','narrative_review','umbrella_review','other_review','not_reported','unclear']}},'evidence':{'type':'array','items':evidence}}),'included_counts':obj({'status':{'type':'string','enum':['reported','not_reported','unclear']},'items':{'type':'array','items':count}}),'warnings':{'type':'array','items':string}})
def main():
 (ROOT/'extraction/schema-v1.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2))
 payload=json.loads((ROOT/'dist/data.json').read_text());rs=[r for f in payload['records_files'] for r in json.loads((ROOT/'dist'/f).read_text())];rng=random.Random(20261009);chosen=[];used=set()
 groups=[('aligners_with_abstract',60,lambda d:'Alinhadores' in d['themes'] and bool(d['abstract'])),('other_themes_with_abstract',30,lambda d:'Alinhadores' not in d['themes'] and bool(d['abstract'])),('missing_abstract',10,lambda d:not d['abstract'])]
 for name,n,pred in groups:
  pool=sorted([d for d in rs if pred(d) and d['id'] not in used],key=lambda d:int(d['id']));rng.shuffle(pool)
  for d in pool[:n]:
   used.add(d['id']);chosen.append({k:d[k] for k in ['id','title','abstract','year','type','themes','hash','url']});chosen[-1]['stratum']=name
 if len(chosen)!=100:raise RuntimeError('Insufficient records for specified pilot')
 plan={'schema_version':'v1','prompt_version':'v1','seed':20261009,'source_run':payload['meta']['run'],'selection':'Operational pilot: seeded sampling within purposive strata; not representative, not a held-out validation sample. 60 aligners with abstracts, 30 other themes with abstracts, 10 missing abstracts. Missing abstracts skip API.','records':chosen}
 (ROOT/'extraction/pilot-v1.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
 (ROOT/'dist/pilot-plan.json').write_text(json.dumps(plan,ensure_ascii=False))
 for f in ['schema-v1.json','prompt-v1.txt']:(ROOT/'dist'/f).write_bytes((ROOT/'extraction'/f).read_bytes())
 print('Prepared 100 records; 90 with abstracts, 10 missing-abstract controls. No paid calls.')
if __name__=='__main__':main()
