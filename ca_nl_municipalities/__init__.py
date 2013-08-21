from utils import CanadianJurisdiction


# The municipal association lists only top-level officials.
# @see http://www.municipalnl.ca/?Content=Contact/Municipal_Directory
class NewfoundlandAndLabrador(CanadianJurisdiction):
  jurisdiction_id = u'ocd-jurisdiction/country:ca/province:nl/legislature'

  def _get_metadata(self):
    return {
      'name': 'Newfoundland Labrador',
      'legislature_name': 'Newfoundland Labrador Municipal Council',
      'legislature_url': 'http://www.ma.gov.nl.ca/ma/municipal_directory/index.html',
    }
