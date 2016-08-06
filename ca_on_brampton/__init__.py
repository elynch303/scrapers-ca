from __future__ import unicode_literals
from utils import CanadianJurisdiction
from pupa.scrape import Organization


class Brampton(CanadianJurisdiction):
    classification = 'legislature'
    division_id = 'ocd-division/country:ca/csd:3521010'
    division_name = 'Brampton'
    name = 'Brampton City Council'
    url = 'http://www.brampton.ca'

    def get_organizations(self):
        organization = Organization(self.name, classification=self.classification)

        organization.add_post(role='Mayor', label=self.division_name, division_id=self.division_id)
        for ward_number in range(1, 11):
            organization.add_post(role='Regional Councillor', label='Ward {}'.format(ward_number))
            organization.add_post(role='Councillor', label='Ward {}'.format(ward_number))

        yield organization
