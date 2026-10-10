"""Versioned, auditable thematic baseline. No LLM; no eligibility inference."""
import re, unicodedata
from functools import lru_cache
VERSION = 'rules-v2'
TAXONOMY = {
 'Alinhadores': ['aligner', 'aligners', 'invisalign'],
 'Aparelhos fixos e técnicas de tratamento': ['bracket', 'brackets', 'fixed appliance', 'fixed appliances', 'lingual orthodontics', 'self ligating', 'straight wire'],
 'Crescimento e ortopedia dentofacial': ['craniofacial growth', 'facial growth', 'skeletal maturation', 'skeletal maturity', 'cervical vertebral', 'functional appliance', 'functional appliances', 'maxillary expansion', 'palatal expansion', 'maxillary protraction', 'headgear', 'dentofacial orthopedics', 'dentofacial orthopaedics', 'alt ramec', 'twin block', 'growth modification'],
 'Maloclusões e relações oclusais': ['malocclusion', 'malocclusions', 'class ii', 'class iii', 'crossbite', 'cross bite', 'open bite', 'deep bite', 'overbite', 'overjet', 'crowding', 'occlusal abnormalities', 'dental occlusion', 'occlusal dysesthesia'],
 'Diagnóstico, imagem e planejamento': ['cephalometric', 'cephalometry', 'cone beam', 'cbct', 'panoramic radiograph', 'panoramic radiographs', 'dental age', 'facial photograph', 'facial photographs', 'orthodontic diagnosis', 'treatment planning', 'diagnostic imaging', 'radiographic assessment'],
 'Biomecânica e ancoragem': ['biomechanics', 'biomechanical', 'finite element', 'anchorage', 'miniscrew', 'miniscrews', 'mini implant', 'mini implants', 'temporary anchorage', 'molar distalization', 'molar distalisation', 'tooth movement', 'tooth movements', 'incisor intrusion', 'intrusion mechanics', 'incisor inclination', 'osseointegration'],
 'Aceleração e terapias adjuvantes': ['accelerated orthodontic', 'orthodontic acceleration', 'corticotomy', 'corticotomies', 'piezocision', 'micro osteoperforation', 'micro osteoperforations', 'photobiomodulation', 'low level laser', 'vibration therapy', 'piezoelectric assisted'],
 'Contenção, recidiva e estabilidade': ['orthodontic retention', 'retainer', 'retainers', 'relapse', 'post treatment stability', 'posttreatment stability', 'orthodontic stability'],
 'Reabsorção radicular e condição pulpar': ['root resorption', 'root resorptions', 'pulpal', 'dental pulp', 'pulp necrosis', 'pulp calcifications', 'pulp vitality', 'endodontic', 'traumatized teeth', 'traumatised teeth'],
 'Periodonto e tecidos de suporte': ['periodontal', 'periodontitis', 'gingival', 'gingivitis', 'alveolar bone', 'supracrestal', 'bone dehiscence', 'bone fenestration'],
 'Cárie, higiene e microbiologia': ['caries', 'carious', 'white spot', 'demineralization', 'demineralisation', 'oral hygiene', 'biofilm', 'biofilms', 'antimicrobial', 'antibacterial', 'microbiome', 'dental plaque'],
 'Materiais, adesão e propriedades mecânicas': ['orthodontic materials', 'dental materials', 'bond strength', 'bonding', 'adhesive', 'adhesives', 'debonding', 'orthodontic wire', 'orthodontic wires', 'archwire', 'archwires', 'ligature', 'ligatures', 'elastomeric', 'nickel titanium', 'glass ionomer', 'corrosion', 'monomer', 'polymer'],
 'IA, tecnologias digitais e impressão 3D': ['artificial intelligence', 'machine learning', 'deep learning', 'large language model', 'large language models', 'chatbot', 'chatbots', 'digital orthodontics', 'digital workflow', 'intraoral scanner', 'intraoral scanners', '3d printing', '3d printed', 'three dimensional printing', 'cad cam', 'computer aided', 'virtual surgical planning', 'augmented reality', 'virtual reality', 'teledentistry', 'teleorthodontics'],
 'Dor e experiência do paciente': ['pain', 'discomfort', 'patient satisfaction', 'patient preference', 'patient preferences', 'patient centered', 'patient centred', 'quality of life', 'psychological', 'psychosocial', 'self esteem', 'anxiety', 'compliance', 'adherence'],
 'Estética facial e do sorriso': ['smile', 'smiles', 'facial aesthetics', 'facial esthetics', 'esthetic', 'aesthetic', 'facial attractiveness', 'lip position', 'soft tissue profile', 'chin augmentation'],
 'Cirurgia ortognática e deformidades dentofaciais': ['orthognathic', 'osteotomy', 'osteotomies', 'le fort', 'genioplasty', 'sagittal split', 'dentofacial deformity', 'dentofacial deformities'],
 'Sono, vias aéreas e respiração': ['sleep apnea', 'sleep apnoea', 'sleep disordered breathing', 'airway', 'airways', 'mandibular advancement device', 'mandibular advancement devices', 'cpap', 'mouth breathing', 'adenotonsillectomy', 'adenoidectomy'],
 'ATM, função e hábitos orais': ['temporomandibular', 'mastication', 'masticatory', 'bruxism', 'myofunctional', 'orofacial myofunctional', 'tongue thrust', 'thumb sucking', 'oral habits', 'swallowing', 'postural control'],
 'Dentes inclusos, erupção e anomalias dentárias': ['impacted', 'impaction', 'tooth eruption', 'dental eruption', 'agenesis', 'hypodontia', 'oligodontia', 'supernumerary', 'infraocclusion', 'autotransplantation', 'auto transplantation', 'tooth transplantation', 'hypomineralisation', 'hypomineralization', 'ectopic eruption', 'transposition'],
 'Extrações, espaço e tratamento interdisciplinar': ['tooth extraction', 'dental extraction', 'premolar extraction', 'premolar extractions', 'extraction of', 'extraction versus', 'extraction vs', 'space closure', 'space management', 'interdisciplinary treatment', 'multidisciplinary treatment', 'prosthodontic', 'restorative treatment'],
 'Fissuras, síndromes e condições especiais': ['cleft', 'clefts', 'craniosynostosis', 'syndrome', 'syndromes', 'craniofacial malformation', 'craniofacial malformations', 'achondroplasia', 'thalassemia', 'hypophosphatemia', 'systemic disease', 'special needs', 'gravid', 'pregnancy'],
 'Epidemiologia, acesso e saúde pública': ['epidemiology', 'epidemiological', 'prevalence of malocclusion', 'orthodontic treatment need', 'orthodontic treatment needs', 'access to care', 'health disparities', 'public health', 'socioeconomic', 'cost effectiveness', 'cost model'],
 'Educação, prática profissional e metapesquisa': ['orthodontic education', 'dental education', 'postgraduate', 'curriculum', 'curricula', 'competencies', 'malpractice', 'guideline', 'guidelines', 'consensus', 'bibliometric', 'research waste', 'reporting quality', 'methodological quality', 'risk of bias', 'systematic reviews in orthodontics'],
 'Biologia, genética e remodelação óssea': ['genetic', 'genetics', 'epigenetic', 'polymorphism', 'polymorphisms', 'bone remodeling', 'bone remodelling', 'stem cell', 'stem cells', 'osteoclast', 'osteoclasts', 'piezo channels', 'extracellular vesicles', 'molecular mechanisms'],
}
@lru_cache(maxsize=32768)
def normalize(s):
 s=unicodedata.normalize('NFKC', s).lower().replace('ⅲ','iii').replace('ⅱ','ii')
 return re.sub(r'[^\w]+',' ',s).strip()
@lru_cache(maxsize=1024)
def pattern(term):
 return re.compile(r'(?<!\w)'+re.escape(normalize(term))+r'(?!\w)')
def matches(term,text):
 return bool(pattern(term).search(text))
def classify(record):
 sources={k:normalize(record.get(k,'') or '') for k in ['title','objective','abstract']}
 mesh=record.get('mesh',[]) or [];out=[]
 for label,terms in TAXONOMY.items():
  hits=[]
  for source in ['title','objective']:
   for term in terms:
    if matches(term,sources[source]):hits.append({'source':source,'term':term})
  for descriptor in mesh:
   for term in terms:
    if matches(term,normalize(descriptor)):hits.append({'source':'mesh','term':term,'descriptor':descriptor})
  abstract_hits=[term for term in terms if matches(term,sources['abstract'])]
  # Abstract alone needs two distinct terms; title/objective/MeSH need one.
  if not hits and len(set(abstract_hits))>=2:hits=[{'source':'abstract','term':t} for t in abstract_hits]
  if hits:out.append({'label':label,'matches':hits,'status':'rule_assigned_unvalidated'})
 fallback='Informação temática insuficiente' if not record.get('abstract') and not mesh else 'Tema não identificado pelas regras'
 return {'themes':[e['label'] for e in out] or [fallback], 'theme':out[0]['label'] if out else fallback,'theme_evidence':out,'theme_version':VERSION,'theme_status':'rule_assigned_unvalidated' if out else 'unclassified'}
