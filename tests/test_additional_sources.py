import json
import sys
import unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
import requests
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scraper'))
from sources import galleries,dice,bachtrack
from main import collect

class AdditionalSourcesTests(unittest.TestCase):
 def test_cross_year_and_no_invented_dates(self):
  self.assertEqual(galleries.dates('7 Oct - 14 Feb 2027'),('2026-10-07','2027-02-14'))
  self.assertEqual(galleries.dates('Closes Sunday, 8 November 2026'),(None,'2026-11-08'))
  self.assertEqual(galleries.dates('Until January 2027'),(None,None))
  self.assertEqual(galleries.dates('Opens 7 November 2026'),(None,None))
 def test_gallery_cards(self):
  html='<a class="exhibiton-carousel-card" href="/exhibitions/x"><h3>Exhibition X</h3><div title="Calendar timing">Closes Sunday, 8 November 2026</div><div title="Venue location">V&amp;A South Kensington</div></a>'
  self.assertEqual(galleries.parse('V&A',html)[0]['venue'],'V&A South Kensington')
  self.assertEqual(galleries.parse('V&A',html.replace('V&amp;A South Kensington','V&amp;A Dundee')),[])
 def test_photo_title_not_promotion_heading(self):
  html='<article class="o-teaser"><span class="o-teaser__post-type">Exhibition</span><h3>Now open!</h3><p class="o-teaser__date">03 Jul 2026 - 13 Sep 2026</p><h3 class="o-teaser__title"><a href="/whats-on/test">Actual artist</a></h3></article>'
  self.assertEqual(galleries.parse("The Photographers' Gallery",html)[0]['title'],'Actual artist')
  self.assertEqual(galleries.parse("The Photographers' Gallery",html.replace('>Exhibition<','>Talks &amp; Events<')),[])
 def test_plain_text_bachtrack_venue(self):
  html='<div data-id="1" data-dates="1789056000"><h2 class="li-shortform-venue">Barbican Hall, <a href="/city/london">London</a></h2><div class="li-shortform-title">Concert</div><a class="listing-more-info" href="/concert-event/test/1">More</a></div>'
  self.assertEqual(bachtrack.parse(html)[0]['venue'],'Barbican Hall')
 def config(self):
  return {'url':'https://dice.fm/event/test','artists':['Chang Kiha'],'subtitle':'장기하','evidence_url':'https://earthackney.co.uk/events/test/','verified_event':{'title':'Chang Kiha','start':'2026-09-28','time':'19:30','venue':'EartH Theatre','verified_at':'2026-09-08T10:00:00+00:00'}}
 def test_dice_london_dates_and_cancelled(self):
  data={'@type':'MusicEvent','name':'Chang Kiha','startDate':'2026-09-28T18:30:00Z','endDate':'2026-09-28T22:00:00Z','location':{'name':'EartH','address':{'addressLocality':'London'}}}
  def html():return '<script type="application/ld+json">'+json.dumps(data)+'</script>'
  ev=dice.parse(html(),self.config());self.assertEqual(ev['time'],'19:30');self.assertEqual(ev['collection'],'korean')
  data['eventStatus']='https://schema.org/EventCancelled';self.assertIsNone(dice.parse(html(),self.config()))
  del data['eventStatus'];data['location']['address']['addressLocality']='Manchester';self.assertIsNone(dice.parse(html(),self.config()))
 def test_manual_verification_is_not_refreshed(self):
  with patch.object(Path,'read_text',return_value=json.dumps({'dice_events':[self.config()]})),patch.object(dice.requests,'get',side_effect=requests.HTTPError('403')):
   result=collect({},[('DICE',dice.fetch)],datetime(2026,9,20,tzinfo=timezone.utc))
  self.assertEqual(result['sources'][0]['status'],'manual')
  self.assertEqual(result['events'][0]['last_seen'],'2026-09-08T10:00:00+00:00')
  self.assertEqual(result['events'][0]['verification_mode'],'manual')

if __name__=='__main__':unittest.main()
