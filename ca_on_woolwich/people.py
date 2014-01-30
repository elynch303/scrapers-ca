from pupa.scrape import Scraper, Legislator

from utils import lxmlize, CONTACT_DETAIL_TYPE_MAP, CONTACT_DETAIL_NOTE_MAP

import re

COUNCIL_PAGE = 'http://www.woolwich.ca/en/council/council.asp'


class WoolwichPersonScraper(Scraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)

    councillors = page.xpath('//div[@id="printArea"]//strong')
    for councillor in councillors:
      info = councillor.xpath('./parent::p/text()')
      if not info:
        info = councillor.xpath('./parent::div/text()')
      info = [x for x in info if x.strip()]
      district = re.sub('(?<=Ward \d+).+', '', info.pop(0))
      if 'Mayor' in district:
        district = 'Woolwich'
        role = 'Mayor'
      else:
        district = district.replace('Councillor', '').strip()
        role = 'Councillor'

      p = Legislator(name=councillor.text_content(), post_id=district, role=role)
      p.add_source(COUNCIL_PAGE)
      p.image = councillor.xpath('./img/@src')[0]

      for contact in info:
        note, num = contact.split(':')
        num = num.strip().replace('(', '').replace(') ', '-').replace('extension ', 'x')
        p.add_contact(CONTACT_DETAIL_TYPE_MAP[note], num, CONTACT_DETAIL_NOTE_MAP[note])
      yield p
