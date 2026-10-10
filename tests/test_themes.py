import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from classify_themes import classify
class Themes(unittest.TestCase):
 def test_multiple_topics(self):
  r=classify({'title':'Root resorption with clear aligners versus fixed appliances'})
  self.assertIn('Alinhadores',r['themes']);self.assertIn('Reabsorção radicular e condição pulpar',r['themes']);self.assertIn('Aparelhos fixos e técnicas de tratamento',r['themes'])
 def test_abstract_incidental_single_term_is_not_enough(self):
  r=classify({'title':'Literature overview','abstract':'Some studies mention pain.'})
  self.assertEqual(r['theme_status'],'unclassified')
 def test_mesh_and_word_boundaries(self):
  r=classify({'title':'Review','mesh':['Sleep Apnea, Obstructive']});self.assertIn('Sono, vias aéreas e respiração',r['themes'])
  r=classify({'title':'Painting instruments'});self.assertNotIn('Dor e experiência do paciente',r['themes'])
 def test_missing_information_separate(self):
  self.assertEqual(classify({'title':'Overview'})['theme'],'Informação temática insuficiente')
  self.assertEqual(classify({'title':'Overview','abstract':'Unrelated text'})['theme'],'Tema não identificado pelas regras')
 def test_greek_class_normalized(self):
  self.assertIn('Maloclusões e relações oclusais',classify({'title':'Class Ⅲ malocclusion'})['themes'])
if __name__=='__main__':unittest.main()
