import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch, Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scraper'))
from curation import classify
from normalize import event, parse_date_range
from main import collect, still_relevant
from sources import bachtrack, ticketmaster

class SelectionTests(unittest.TestCase):
    def music(self,title,**kw):
        return dict(category='music',title=title,source='Ticketmaster',type='Rock',venue='London',start='2026-10-01',end='2026-10-01',url='https://example.com',**kw)
    def test_watchlist_and_tribute(self):
        self.assertEqual(classify(self.music('Bon Jovi',artists=['Bon Jovi']))['collection'],'headliners')
        self.assertIsNone(classify(self.music('Bon Jovi Tribute',artists=['Bon Jovi'])))
        self.assertIsNone(classify(self.music('Unrelated rock band')))
    def test_korean_without_false_dean_match(self):
        self.assertIsNone(classify(self.music('Saturday Jazz Lunch | Frank & Dean')))
        self.assertEqual(classify(self.music('DEAN',artists=['DEAN']))['collection'],'korean')
        self.assertEqual(classify(self.music('ITZY World Tour'))['genre'],'K-pop')
        self.assertIsNone(classify(self.music('ITZY - Venue Premium Tickets')))
    def test_classical_not_all_recommended(self):
        ev=self.music('Local Mozart recital');ev.update(source='Bachtrack',type='Classical')
        self.assertFalse(classify(ev)['featured'])
        ev['subtitle']='Vikingur Olafsson, piano'
        self.assertTrue(classify(ev)['featured'])
    def test_genres(self):
        ev=self.music('The Rose',artists=['The Rose']);ev['type']='Alternative Rock'
        self.assertEqual(classify(ev)['genre'],'Rock')
    def test_dates_and_performance_identity(self):
        self.assertEqual(parse_date_range('2026-10-01')[:2],('2026-10-01','2026-10-01'))
        self.assertEqual(parse_date_range('25 Jun 2026 - 3 Jan 2027')[:2],('2026-06-25','2027-01-03'))
        self.assertFalse(still_relevant({'start':'2026-09-01'},date(2026,9,8)))
        self.assertFalse(still_relevant({},date(2026,9,8)))
        self.assertTrue(still_relevant({'end':'2026-09-08'},date(2026,9,8)))
        a=event('music','X','https://example.com','Bachtrack',start='2026-10-01',time='13:00')
        b=event('music','X','https://example.com','Bachtrack',start='2026-10-01',time='19:00')
        self.assertNotEqual(a['id'],b['id'])
    def test_source_retention_expires(self):
        ev=self.music('Bon Jovi');now=datetime(2026,9,8,tzinfo=timezone.utc)
        previous={'updated':'2026-09-07 11:40 UTC','events':[ev]}
        def failed(): raise RuntimeError('Unavailable')
        p=collect(previous,[('Ticketmaster',failed)],now)
        self.assertEqual(len(p['events']),1);self.assertTrue(p['events'][0]['stale'])
        p=collect(p,[('Ticketmaster',failed)],datetime(2026,9,16,tzinfo=timezone.utc))
        self.assertEqual(p['events'],[])
    def test_successful_empty_clears_old_concerts(self):
        previous={'updated':'2026-09-07 11:40 UTC','events':[self.music('Bon Jovi')]}
        p=collect(previous,[('Ticketmaster',lambda:[])],datetime(2026,9,8,tzinfo=timezone.utc))
        self.assertEqual(p['events'],[]);self.assertEqual(p['sources'][0]['status'],'ok')
    def test_bachtrack_dates_and_pagination_envelope(self):
        html='''<div data-id="1" data-dates="1789056000,1789059600"><h2 class="li-shortform-venue"><a>Royal Festival Hall</a></h2><div class="li-shortform-title">Test recital</div><a class="listing-more-info" href="/concert-event/test/1">More</a><div class="listing-personnel-simple"><div class="item">Yuja Wang</div></div></div>'''
        events=bachtrack.parse(html)
        self.assertEqual([e['time'] for e in events],['17:00','18:00'])
        self.assertEqual(len({e['id'] for e in events}),2)
        first=Mock(text=html+'<button class="btk-search-more" data-startrow="50" data-param="category=1;city=london"></button>')
        second=Mock();second.json.return_value={'result':'OK','data':{'count':1,'total':51,'text':html}}
        with patch.object(bachtrack.requests,'Session') as session,patch.object(bachtrack.time,'sleep'):
            session.return_value.get.side_effect=[first,second]
            self.assertEqual(len(bachtrack.fetch()),4)
            self.assertEqual(session.return_value.get.call_count,2)
    def test_cancelled_ticketmaster_is_excluded(self):
        self.assertIsNone(ticketmaster.parse({'dates':{'status':{'code':'cancelled'}}}))

if __name__=='__main__':unittest.main()
