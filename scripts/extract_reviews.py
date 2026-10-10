#!/usr/bin/env python3
"""Offline preflight by default. Explicit execution only; never automatic retries."""
import argparse,json,hashlib,os,math,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone,date
ROOT=Path(__file__).resolve().parents[1]
FIELDS=['objective','population','intervention_or_exposure','comparator','outcomes','context']
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def validate_shape(value,s):
 types=s['type'] if isinstance(s['type'],list) else [s['type']]
 valid=any((t=='null' and value is None) or (t=='object' and isinstance(value,dict)) or (t=='array' and isinstance(value,list)) or (t=='string' and isinstance(value,str)) or (t=='integer' and isinstance(value,int) and not isinstance(value,bool)) for t in types)
 if not valid:raise ValueError('Schema type mismatch')
 if 'enum' in s and value not in s['enum']:raise ValueError('Invalid enum')
 if isinstance(value,dict):
  if set(value)!=set(s['required']):raise ValueError('Missing or unexpected fields')
  for k,v in value.items():validate_shape(v,s['properties'][k])
 if isinstance(value,list):
  for item in value:validate_shape(item,s['items'])
def validate(result,record,schema):
 validate_shape(result,schema)
 def quote(e):
  if not e['quote'] or e['quote'] not in record[e['source']]:raise ValueError('Evidence is not an exact source substring')
 for name in FIELDS:
  f=result[name]
  for e in f['evidence']:quote(e)
  if f['status']=='reported' and (not f['value'] or not f['evidence']):raise ValueError('Reported field lacks value or evidence')
  if f['status']!='reported' and f['value'] is not None:raise ValueError('Non-reported field must be null')
  if f['status']=='not_reported' and f['evidence']:raise ValueError('Missing field has evidence')
 rt=result['review_types']
 if not rt['values']:raise ValueError('Review type cannot be empty')
 for e in rt['evidence']:quote(e)
 if any(t not in ['not_reported','unclear'] for t in rt['values']) and not rt['evidence']:raise ValueError('Type lacks evidence')
 if 'document_kind' in result:
  for ev in result['document_kind']['evidence']:quote(ev)
  if result['document_kind']['value'] not in ['not_reported','unclear'] and not result['document_kind']['evidence']:raise ValueError('Document kind lacks evidence')
  for item in result['search_end_dates']:
   quote(item['evidence']);date.fromisoformat(item['date_iso'])
  f=result['comparator']
  if f['status']=='reported' and f['kind'] in ['not_reported','unclear']:raise ValueError('Reported comparator needs a kind')
  if f['status']!='reported' and f['kind']!=f['status']:raise ValueError('Comparator status/kind mismatch')
 cs=result['included_counts']
 if cs['status']=='reported' and not cs['items']:raise ValueError('Reported count lacks items')
 if cs['status']=='not_reported' and cs['items']:raise ValueError('Missing count has items')
 for c in cs['items']:
  if c['number']<0:raise ValueError('Negative included count')
  quote(c['evidence'])
 return result

def date_checks(result,execution_date):
 today=date.fromisoformat(execution_date)
 return [{'date_iso':item['date_iso'],'is_future':date.fromisoformat(item['date_iso'])>today,'execution_date':execution_date,'evidence':item['evidence']} for item in result.get('search_end_dates',[])]

def request_body(record,config,prompt,schema):
 return {'model':config['model'],'store':False,'instructions':prompt,'input':json.dumps({'title':record['title'],'abstract':record['abstract']},ensure_ascii=False),'max_output_tokens':config['max_output_tokens'],'reasoning':{'effort':config.get('reasoning_effort','low')},'text':{'format':{'type':'json_schema','name':'orthodontic_review_extraction','strict':True,'schema':schema}}}
def cache_key(record,config,prompt,schema):
 return digest({'provider':'OpenAI Responses','model':config['model'],'title':record['title'],'abstract':record['abstract'],'prompt':prompt,'schema':schema,'max_output_tokens':config['max_output_tokens'],'reasoning_effort':config.get('reasoning_effort','low')})
def estimate(records,config,prompt,schema):
 eligible=[r for r in records if r['abstract']];schema_bytes=len(json.dumps(schema,ensure_ascii=False).encode());prompt_bytes=len(prompt.encode())
 # Planning proxy, NOT tokenizer-exact billing; 25% planning margin.
 input_estimate=sum(math.ceil((prompt_bytes+schema_bytes+len(json.dumps({'title':r['title'],'abstract':r['abstract']},ensure_ascii=False).encode())+200)/4*1.25) for r in eligible)
 output_estimate=len(eligible)*config['expected_output_tokens'];output_limit=len(eligible)*config['max_output_tokens']
 ir,orr=config.get('input_usd_per_million'),config.get('output_usd_per_million');priced=ir is not None and orr is not None
 return {'eligible_requests':len(eligible),'skip_missing_abstract':len(records)-len(eligible),'input_tokens_planning_proxy':input_estimate,'output_tokens_expected':output_estimate,'output_tokens_configured_limit':output_limit,'expected_usd':round((input_estimate*ir+output_estimate*orr)/1e6,4) if priced else None,'planning_usd_at_output_limit':round((input_estimate*ir+output_limit*orr)/1e6,4) if priced else None,'note':'Input proxy uses UTF-8 bytes/4 + 25% margin, not tokenizer counts or a guaranteed spending cap. Output limit includes model output/reasoning as billed by selected model. No discount assumed; enter current standard API rates. Model and tariffs unset means no dollar estimate.'}
def atomic(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));tmp.replace(path)
def parse_response(raw):
 if raw.get('status')!='completed':raise ValueError('Response incomplete or failed')
 texts=[]
 for item in raw.get('output',[]):
  for part in item.get('content',[]):
   if part.get('type')=='refusal':raise ValueError('Model refused extraction')
   if part.get('type')=='output_text':texts.append(part['text'])
 if not texts:raise ValueError('No structured output')
 return json.loads(''.join(texts))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=ROOT/'extraction/config.example.json');ap.add_argument('--plan',type=Path,default=ROOT/'extraction/pilot-v1.json');ap.add_argument('--prompt',type=Path);ap.add_argument('--schema',type=Path);ap.add_argument('--execute',action='store_true');ap.add_argument('--max-requests',type=int,default=0);ap.add_argument('--output',type=Path,default=ROOT/'extraction/results');a=ap.parse_args()
 config=json.loads(a.config.read_text());plan=json.loads(a.plan.read_text());version=plan.get('schema_version','v1');prompt=(a.prompt or ROOT/('extraction/prompt-'+plan.get('prompt_version',version)+'.txt')).read_text();schema=json.loads((a.schema or ROOT/('extraction/schema-'+version+'.json')).read_text());records=plan['records']
 for k in ['input_usd_per_million','output_usd_per_million']:
  if config.get(k) is not None and (not isinstance(config[k],(int,float)) or config[k]<0):raise SystemExit('Invalid price')
 if not 1<=config['expected_output_tokens']<=config['max_output_tokens']:raise SystemExit('Invalid token limits')
 pending=[];cached=0;attempted=0
 for r in records:
  if not r['abstract']:continue
  key=cache_key(r,config,prompt,schema);path=a.output/'cache'/f'{key}.json';journal=a.output/'attempts'/f'{key}.json'
  if path.exists():validate(json.loads(path.read_text())['extraction'],r,schema);cached+=1
  elif journal.exists():attempted+=1
  else:pending.append(r)
 report=estimate(pending,config,prompt,schema);report.update({'mode':'preflight','pilot_size':len(records),'cached':cached,'previous_attempts_not_retried':attempted,'missing_abstracts_total':sum(not r['abstract'] for r in records),'source_run':plan['source_run'],'model':config['model']});atomic(ROOT/'extraction/preflight.json',report);atomic(ROOT/'dist/extraction-preflight.json',report)
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if not a.execute:return
 if not config.get('api_execution_enabled') or not config.get('model') or not config.get('pricing_checked_at') or config.get('input_usd_per_million') is None or config.get('output_usd_per_million') is None or a.max_requests<1:raise SystemExit('Execution requires explicitly enabled config, model, dated prices and --max-requests > 0')
 secret=os.environ.get('OPENAI_API_KEY')
 if not secret:raise SystemExit('Set OPENAI_API_KEY securely in the processing environment')
 billed=[]
 for r in pending[:a.max_requests]:
  key=cache_key(r,config,prompt,schema);journal=a.output/'attempts'/f'{key}.json';stamp={'pmid':r['id'],'source_run':plan['source_run'],'source_hash':r['hash'],'cache_key':key,'started_at':datetime.now(timezone.utc).isoformat(),'status':'started_no_automatic_retry'};journal.parent.mkdir(parents=True,exist_ok=True)
  lock=journal.with_suffix('.lock')
  try:
   fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
  except FileExistsError:
   print('Existing attempt lock; skipping PMID '+r['id']);continue
  atomic(journal,stamp)
  body=request_body(r,config,prompt,schema)
  try:
   req=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+secret,'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=180) as response:raw=json.loads(response.read())
   atomic(a.output/'raw'/f'{key}.json',raw);usage=raw.get('usage',{});billed.append({'pmid':r['id'],'usage':usage,'response_id':raw.get('id'),'standard_rate_cost_proxy_usd':(usage.get('input_tokens',0)*config['input_usd_per_million']+usage.get('output_tokens',0)*config['output_usd_per_million'])/1e6});stamp.update({'response_id':raw.get('id'),'usage':usage});result=validate(parse_response(raw),r,schema)
   atomic(a.output/'cache'/f'{key}.json',{'metadata':{**stamp,'model_requested':config['model'],'model_returned':raw.get('model'),'prompt_hash':digest(prompt),'schema_hash':digest(schema),'status':'machine_extracted_unvalidated','date_checks':date_checks(result,datetime.now(timezone.utc).date().isoformat())},'extraction':result});stamp['status']='completed'
  except Exception as e:
   # Store no exception text that might contain request credentials.
   stamp['status']='failed_requires_manual_review';stamp['error_class']=type(e).__name__;atomic(journal,stamp);atomic(a.output/'usage.json',billed);raise SystemExit('Request or validation failed. Preserved attempt/available response; no automatic retry.')
  atomic(journal,stamp);atomic(a.output/'usage.json',billed);print('Saved extraction for PMID '+r['id'],flush=True)
if __name__=='__main__':main()
