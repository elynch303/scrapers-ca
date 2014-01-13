from pupa.scrape import Scraper, Legislator

from utils import lxmlize, CanadianScraper

import re

COUNCIL_PAGE = 'http://www.villagesenneville.qc.ca/fr/membres-du-conseil-municipal'


class SennevillePersonScraper(CanadianScraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)

    councillors = page.xpath('//div[@class="field-item even"]//tr')
    for councillor in councillors:
      district = councillor.xpath('./td[1]//strong/text()')[0]
      role = 'Councillor'
      if 'Maire' in district:
        district = 'senneville'
        role = 'Mayor'
      name = councillor.xpath('./td[2]//strong/text()')[0].lower()
      email = councillor.xpath('.//a/text()')[0]
      p = Legislator(name=name, post_id=district)
      p.add_source(COUNCIL_PAGE)
      p.role = role
      p.image = councillor.xpath('.//img/@src')[0]
      p.add_contact('email', email, None)
      yield p
