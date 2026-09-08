import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scraper'))
from sources.live_music import ronnie_dates, clock, parse
from curation import classify
class LiveMusicTests(unittest.TestCase):
 def test_recurring_span(self):
  self.assertEqual(ronnie_dates('Wed 9 – Wed 30 Sept 2026'),('2026-09-09','2026-09-30'))
  self.assertEqual(ronnie_dates('Wed9 - Wed30Sept2026'),('2026-09-09','2026-09-30'))
 def test_year_boundary(self):
  self.assertEqual(ronnie_dates('31 Dec – 2 Jan 2027'),('2026-12-31','2027-01-02'))
 def test_no_year(self):
  self.assertEqual(ronnie_dates('9 Sept'),(None,None))
 def test_clock(self):
  self.assertEqual(clock('7.45 - 10.30PM'),'19:45')
  self.assertEqual(clock('11 - 1AM'),'')
 def test_jazz_not_watchlist_limited(self):
  e=classify(dict(category='music',title='New Jazz Quartet',type='Jazz'))
  self.assertEqual(e['collection'],'jazz')
 def test_discovery_and_korean(self):
  e=classify(dict(category='music',title='Ampers&One in London',type='Other',discovery=True))
  self.assertEqual(e['collection'],'korean')
  self.assertTrue(e['discovery'])
  self.assertIsNone(classify(dict(category='music',title='Unknown',type='Rock')))
 def test_non_london_serious_excluded(self):
  self.assertEqual(parse('Serious','<a class="listing-event" href="https://example.com"><h2>Concert</h2><span class="min-width-pill">Strange Brew</span><time datetime="2026-11-28"></time></a>'),[])
if __name__=='__main__':unittest.main()
