from __future__ import unicode_literals
from utils import CanadianJurisdiction
from pupa.scrape import Organization


class Lambton(CanadianJurisdiction):
    classification = 'legislature'
    division_id = 'ocd-division/country:ca/cd:3538'
    division_name = 'Lambton'
    name = 'Lambton County Council'
    url = 'http://www.lambtononline.ca/home/government/accessingcountycouncil/countycouncillors/Pages/default.aspx'

    def get_organizations(self):
        organization = Organization(self.name, classification=self.classification)

        organization.add_post(role='Warden', label='Lambton')
        organization.add_post(role='Deputy Warden', label='Lambton')
        for i in range(15):
            organization.add_post(role='Councillor', label='Lambton (seat %d)' % (i + 1))

        yield organization
