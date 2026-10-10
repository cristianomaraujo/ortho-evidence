#!/usr/bin/env python3
"""Reproducible PubMed collection and exploratory TF-IDF baseline; not validated."""
import sys
from classify_themes import classify
import numpy as np
import urllib.request,urllib.parse,json,time,re,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
ROOT=Path(__file__).resolve().parents[1]
ORTHODONTIC_TERMS='("Orthodontics"[MeSH Terms] OR "Orthodontic Appliances"[MeSH Terms] OR "Malocclusion"[MeSH Terms] OR "Tooth Movement Techniques"[MeSH Terms] OR orthodontic*[Title/Abstract] OR dentofacial orthop*[Title/Abstract] OR malocclusion*[Title/Abstract] OR clear aligner*[Title/Abstract] OR Invisalign[Title/Abstract] OR orthognathic[Title/Abstract])'
SCOPING_FILTER='("scoping review*"[Title/Abstract] OR "scoping literature review*"[Title/Abstract] OR "systematic scoping review*"[Title/Abstract] OR "mapping review*"[Title/Abstract] OR "systematic map*"[Title/Abstract] OR "evidence map*"[Title/Abstract])'
TYPED_FILTER='("Review"[Publication Type] OR "Systematic Review"[Publication Type] OR "Meta-Analysis"[Publication Type])'
REVIEW_FILTER='("Review"[Publication Type] OR "Systematic Review"[Publication Type] OR "Meta-Analysis"[Publication Type] OR systematic[sb] OR '+SCOPING_FILTER+')'
QUERY=ORTHODONTIC_TERMS+' AND '+REVIEW_FILTER

def get(endpoint,params):
 u='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'+endpoint+'?'+urllib.parse.urlencode(params)
 for attempt in range(4):
  try:
   with urllib.request.urlopen(u,timeout=90) as r:return r.read()
  except Exception:
   if attempt==3:raise
   time.sleep(2**attempt)
def txt(el):return ''.join(el.itertext()).strip() if el is not None else ''

def process(el):
 c=el.find('MedlineCitation');a=c.find('Article');pmid=txt(c.find('PMID'));title=txt(a.find('ArticleTitle'))
 parts=[(x.get('Label',''),txt(x)) for x in a.findall('Abstract/AbstractText')];abstract=' '.join((l+': ' if l else '')+s for l,s in parts)
 objectives=' '.join(s for l,s in parts if re.search('objective|aim|purpose',l,re.I))
 if not objectives:
  ss=re.split(r'(?<=[.!?])\s+',abstract);objectives=' '.join(s for s in ss if re.search(r'\b(aim(?:ed|s)?|objective|purpose)\b',s,re.I))
 evidence=[]
 for s in re.split(r'(?<=[.!?])\s+',abstract):
  for m in re.finditer(r'\b(\d+)\s+(?:(?:eligible|primary|clinical|randomi[sz]ed|controlled|observational)\s+){0,3}(studies|articles|trials|publications)\s+(?:were\s+|was\s+)?(?:included|eligible|selected)',s,re.I):
   evidence.append({'n':int(m.group(1)),'unit':m.group(2).lower(),'quote':s,'status':'automatic_unvalidated'})
  for m in re.finditer(r'\bincluded\s+(?:a total of\s+)?(\d+)\s+(studies|articles|trials|publications)\b',s,re.I):
   evidence.append({'n':int(m.group(1)),'unit':m.group(2).lower(),'quote':s,'status':'automatic_unvalidated'})
 evidence=list({(x['n'],x['unit'],x['quote']):x for x in evidence}.values())
 doi=next((txt(x) for x in el.findall('PubmedData/ArticleIdList/ArticleId') if x.get('IdType')=='doi'),'')
 date=a.find('Journal/JournalIssue/PubDate');ys=txt(date.find('Year')) if date is not None else ''
 if not ys and date is not None:
  m=re.search(r'\b(19|20)\d{2}\b',txt(date));ys=m.group() if m else ''
 record={'id':pmid,'pmid':pmid,'title':title,'year':int(ys) if ys.isdigit() else 0,'journal':txt(a.find('Journal/Title')),'type':'; '.join(txt(x) for x in a.findall('PublicationTypeList/PublicationType')),'url':'https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/','doi':doi,'abstract':abstract,'objective':objectives,'counts':evidence,'mesh':[txt(x.find('DescriptorName')) for x in c.findall('MeshHeadingList/MeshHeading')],'status':'Registro recuperado; elegibilidade e extração não validadas','hash':hashlib.sha256(ET.tostring(el)).hexdigest()}
 record.update(classify(record));return record
def write_dataset(payload):
 records=payload.pop('records');files=[]
 for start in range(0,len(records),2000):
  name=f'records-{start//2000}.json';files.append(name)
  (ROOT/'dist'/name).write_text(json.dumps(records[start:start+2000],ensure_ascii=False))
 payload['records_files']=files
 (ROOT/'dist'/'data.json').write_text(json.dumps(payload,ensure_ascii=False))
def main():
 previous=None
 if '--from-cache' in sys.argv:
  raw=sorted((ROOT/'data'/'raw').iterdir())[-1];run=raw.name
  roots=[ET.parse(f).getroot() for f in sorted(raw.glob('*.xml'),key=lambda f:int(f.stem))]
  ids=[txt(x.find('MedlineCitation/PMID')) or txt(x.find('BookDocument/PMID')) for root in roots for x in root]
  search=json.loads((raw/'search.json').read_text()) if (raw/'search.json').exists() else {'count':str(len(ids)),'idlist':ids,'querytranslation':QUERY}
 else:
  search=json.loads(get('esearch.fcgi',{'db':'pubmed','term':QUERY,'retmode':'json','retmax':9999,'sort':'pub date','usehistory':'y'}))['esearchresult'];ids=search['idlist']
  if int(search['count'])!=len(ids):raise RuntimeError('Incomplete ID retrieval')
  previous=sorted((ROOT/'data'/'raw').iterdir())[-1] if '--reuse-cache' in sys.argv else None
  run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');raw=ROOT/'data'/'raw'/run;raw.mkdir(parents=True,exist_ok=True);roots=[]
  (raw/'search.json').write_text(json.dumps(search))
  (raw/'query.txt').write_text(QUERY)
  print('PubMed count:',search['count'],flush=True)
  fetch_ids=ids
  if previous:
   cached=[]
   for f in sorted(previous.glob('*.xml'),key=lambda f:int(f.stem)):
    root=ET.parse(f).getroot()
    for x in list(root):
     pid=txt(x.find('MedlineCitation/PMID')) or txt(x.find('BookDocument/PMID'))
     if pid in set(ids):cached.append(x)
   for cache_start in range(0,len(cached),400):
    cache_root=ET.Element('PubmedArticleSet');cache_root.extend(cached[cache_start:cache_start+400]);ET.ElementTree(cache_root).write(raw/f'{cache_start}.xml',encoding='utf-8');roots.append(cache_root)
   cached_ids={txt(x.find('MedlineCitation/PMID')) or txt(x.find('BookDocument/PMID')) for x in cached}
   fetch_ids=[pid for pid in ids if pid not in cached_ids]
   print('Reused cached records:',len(cached),'New records:',len(fetch_ids),flush=True)
  for start in range(0,len(fetch_ids),400):
   body=get('efetch.fcgi',({'db':'pubmed','id':','.join(fetch_ids[start:start+400]),'retmode':'xml'} if previous else {'db':'pubmed','query_key':search['querykey'],'WebEnv':search['webenv'],'retstart':start,'retmax':400,'retmode':'xml'}));(raw/f'{start+len(cached) if previous else start}.xml').write_bytes(body);roots.append(ET.fromstring(body));print('Fetched:',start+len(roots[-1]),flush=True);time.sleep(.4)
 provenance_path=raw/'retrieval_sets.json'
 if provenance_path.exists():retrieval_sets=json.loads(provenance_path.read_text())
 else:
  retrieval_sets={}
  for name,filter_query in [('publication_type',TYPED_FILTER),('systematic_filter','systematic[sb]'),('scope_mapping_terms',SCOPING_FILTER)]:
   q=ORTHODONTIC_TERMS+' AND '+filter_query
   result=json.loads(get('esearch.fcgi',{'db':'pubmed','term':q,'retmode':'json','retmax':9999}))['esearchresult']
   if int(result['count'])!=len(result['idlist']):raise RuntimeError('Incomplete provenance retrieval')
   retrieval_sets[name]={'query':q,'ids':result['idlist']}
   time.sleep(.4)
  provenance_path.write_text(json.dumps(retrieval_sets))
 route_sets={name:set(entry['ids']) for name,entry in retrieval_sets.items()}
 records=[process(x) for root in roots for x in root.findall('PubmedArticle')]
 excluded=[{'pmid':txt(x.find('BookDocument/PMID')),'reason':'PubmedBookArticle: book/report; outside journal-article parser; eligibility requires review'} for root in roots for x in root.findall('PubmedBookArticle')]
 retrieved_ids=[d['id'] for d in records]+[d['pmid'] for d in excluded]
 if len(retrieved_ids)!=len(ids) or len(set(retrieved_ids))!=len(ids) or set(retrieved_ids)!=set(ids):raise RuntimeError('Incomplete or duplicate record retrieval')
 for d in records:
  d['retrieval_routes']=[name for name,member_ids in route_sets.items() if d['id'] in member_ids]
  d['free_text_only']=d['retrieval_routes']==['scope_mapping_terms']
  text=d['title']+' '+d['abstract'];d['review_family_signals']=[]
  if re.search(r'\b(?:systematic\s+)?scoping(?:\s+literature)?\s+reviews?\b',text,re.I):d['review_family_signals'].append('Revisão de escopo')
  if re.search(r'\b(?:mapping\s+reviews?|(?:systematic|evidence)\s+maps?)\b',text,re.I):d['review_family_signals'].append('Mapa de evidências')
 vectorizer=TfidfVectorizer(stop_words='english',ngram_range=(1,2),min_df=2,max_df=.95,max_features=30000)
 matrix=vectorizer.fit_transform([d['title']+' '+(d['objective'] or d['abstract']) for d in records])
 for start in range(0,len(records),100):
  sim=cosine_similarity(matrix[start:start+100],matrix)
  for offset,row in enumerate(sim):
   i=start+offset;k=min(9,len(row));candidates=np.argpartition(row,-k)[-k:];order=candidates[np.argsort(row[candidates])[::-1]];records[i]['similar']=[{'id':records[j]['id'],'score':round(float(row[j]),4)} for j in order if j!=i][:8]
 from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
 for i,d in enumerate(records):
  row=matrix.getrow(i);d['vector']=[[int(k),round(float(v),6)] for k,v in zip(row.indices,row.data)]
 vocab={term:[int(k),float(vectorizer.idf_[k])] for term,k in vectorizer.vocabulary_.items()}
 payload={'index':{'vocab':vocab,'stopwords':sorted(ENGLISH_STOP_WORDS)},'meta':{'query':(raw/'query.txt').read_text() if (raw/'query.txt').exists() else QUERY,'query_translation':search.get('querytranslation'),'reused_snapshot':previous.name if '--reuse-cache' in sys.argv and previous else None,'retrieval_routes':'Exact ESearch membership: publication types, systematic filter, scope/mapping free terms. Text family signals are unvalidated, not confirmed review designs.','retrieved_at':datetime.now(timezone.utc).isoformat(),'excluded_record_types':excluded,'retrieved_count':len(records),'pubmed_count':int(search['count']),'eligibility':'Not manually verified','method':'TF-IDF word 1–2 grams + cosine similarity; exploratory unvalidated baseline','themes':'rules-v2: title, objective, abstract and MeSH; unvalidated; multiple labels','counts':'Explicit numeric patterns, source sentences retained; unvalidated','automatic_schedule':False,'run':run},'records':records}
 write_dataset(payload);(raw/'search.json').write_text(json.dumps(search));print('Complete:',len(records),flush=True)
if __name__=='__main__':main()
