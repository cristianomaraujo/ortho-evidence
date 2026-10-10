"""Reclassify saved records without recollection, vectors or source-hash changes."""
import json,collections
from pathlib import Path
from datetime import datetime,timezone
from classify_themes import classify,VERSION,TAXONOMY
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=ROOT/'dist/data.json';payload=json.loads(p.read_text());before=collections.Counter();after=collections.Counter();total=0;unclassified=0
 for file in payload['records_files']:
  f=ROOT/'dist'/file;records=json.loads(f.read_text())
  for r in records:
   before[r['theme']]+=1;r.update(classify(r));after.update(r['themes']);total+=1;unclassified+=r['theme_status']=='unclassified'
  tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(records,ensure_ascii=False,separators=(',',':')));tmp.replace(f)
 payload['meta'].update({'themes':'rules-v2: title, objective, abstract and MeSH; unvalidated; multiple labels','theme_version':VERSION,'theme_updated_at':datetime.now(timezone.utc).isoformat(),'theme_categories':len(TAXONOMY),'theme_unclassified':unclassified})
 p.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
 report={'version':VERSION,'total':total,'previous_primary_counts':dict(before),'new_multilabel_counts':dict(after),'unclassified':unclassified,'note':'Rule coverage, not accuracy. Counts overlap. Source run and hashes unchanged.'}
 (ROOT/'dist/theme-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(ROOT/'dist/taxonomy.json').write_text(json.dumps({'version':VERSION,'categories':TAXONOMY},ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
