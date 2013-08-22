from pupa.scrape import Scraper, Legislator

from utils import lxmlize

import re

COUNCIL_PAGE = 'http://www.township.wellesley.on.ca/index.php?file=council/council.html'


class WellesleyPersonScraper(Scraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)

    councillors = page.xpath('//table[@class="tbl w100"][2]//tr/td')[1::2]
    councillors = councillors + page.xpath('//table[@class="tbl w100"][1]//td[2]')
    for councillor in councillors:
      district = councillor.xpath('./preceding-sibling::td/text()')
      if district:
        district = district[-1]
      else:
        district = 'wellesley'
      name = councillor.xpath('./span/text()')[0] 
      address = councillor.xpath('./text()')
      address = re.sub(r'\s{2,}', ' ', ' '.join(address[:4]))
      phone = councillor.xpath('./text()')[4].strip().replace('.','-')
      email = councillor.xpath('./a/text()')[0]

      p = Legislator(name=name, post_id=district)
      p.add_source(COUNCIL_PAGE)
      p.add_contact('address', address, None)
      p.add_contact('phone', phone, None)
      p.add_contact('email', email, None)
      yield p