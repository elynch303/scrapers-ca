# coding: utf-8
from __future__ import unicode_literals

import codecs
import csv
import importlib
import os
import re
import string

import lxml.html
import requests
from invoke import run, task
from six import next, StringIO, text_type
from six.moves.urllib.parse import urlsplit
from unidecode import unidecode


# Map Standard Geographical Classification codes to the OCD identifiers of provinces and territories.
province_and_territory_codes_memo = {}


def province_and_territory_codes():
  if not province_and_territory_codes_memo:
    reader = csv_reader('https://raw.github.com/opencivicdata/ocd-division-ids/master/identifiers/country-ca/ca_provinces_and_territories.csv')
    next(reader)
    for row in reader:
      province_and_territory_codes_memo[row[4]] = row[0]
  return province_and_territory_codes_memo


def csv_reader(url):
  """
  Reads a remote CSV file.
  """
  return csv.reader(StringIO(requests.get(url).text))


def slug(name):
  return unidecode(text_type(name).lower().translate({
    ord(' '): '_',
    ord("'"): '_',
    ord('-'): '_',  # dash
    ord('—'): '_',  # m-dash
    ord('–'): '_',  # n-dash
    ord('.'): None,
  }))

urls_memo = {}
ocdid_to_type_name_map = {}
ocdid_to_name_map = {}


def get_definition(division_id, aggregation=False):
  if not urls_memo:
    # Map OCD identifiers to URLs.
    reader = csv_reader('https://raw.github.com/opencivicdata/ocd-division-ids/master/identifiers/country-ca/ca_census_subdivisions-url.csv')
    next(reader)
    for row in reader:
      urls_memo[row[0]] = row[1]
    reader = csv_reader('https://raw.github.com/opencivicdata/ocd-division-ids/master/identifiers/country-ca/census_subdivision-montreal-boroughs-url.csv')
    next(reader)
    for row in reader:
      urls_memo[row[0]] = row[1]

  if not ocdid_to_type_name_map:
    # Map census division type codes to names.
    census_division_type_names = {}
    document = lxml.html.fromstring(requests.get('http://www12.statcan.gc.ca/census-recensement/2011/ref/dict/table-tableau/table-tableau-4-eng.cfm').content)
    for abbr in document.xpath('//table/tbody/tr/th[1]/abbr'):
      census_division_type_names[abbr.text_content()] = re.sub(' /.+\Z', '', abbr.attrib['title'])

    # Map OCD identifiers to census division types.
    reader = csv_reader('https://raw.github.com/opencivicdata/ocd-division-ids/master/identifiers/country-ca/ca_census_divisions.csv')
    next(reader)
    for row in reader:
      ocdid_to_type_name_map[row[0]] = census_division_type_names[row[3]]

    # Map census subdivision type codes to names.
    census_subdivision_type_names = {}
    document = lxml.html.fromstring(requests.get('http://www12.statcan.gc.ca/census-recensement/2011/ref/dict/table-tableau/table-tableau-5-eng.cfm').content)
    for abbr in document.xpath('//table/tbody/tr/th[1]/abbr'):
      census_subdivision_type_names[abbr.text_content()] = re.sub(' /.+\Z', '', abbr.attrib['title'])

    # Map OCD identifiers to census subdivision types.
    reader = csv_reader('https://raw.github.com/opencivicdata/ocd-division-ids/master/identifiers/country-ca/ca_census_subdivisions.csv')
    next(reader)
    for row in reader:
      ocdid_to_type_name_map[row[0]] = census_subdivision_type_names[row[3]]

  # Map OCD identifiers and Standard Geographical Classification codes to names.
  if not ocdid_to_name_map:
    ocdid_to_name_map['ocd-division/country:ca'] = 'Canada'
    reader = csv_reader('https://raw.github.com/opencivicdata/ocd-division-ids/master/identifiers/country-ca/census_subdivision-montreal-boroughs.csv')
    next(reader)
    for row in reader:
      ocdid_to_name_map[row[0]] = row[1]
    reader = csv_reader('https://raw.github.com/opencivicdata/ocd-division-ids/master/identifiers/country-ca/ca_provinces_and_territories.csv')
    next(reader)
    for row in reader:
      ocdid_to_name_map[row[0]] = row[1]
    reader = csv_reader('https://raw.github.com/opencivicdata/ocd-division-ids/master/identifiers/country-ca/ca_census_divisions.csv')
    next(reader)
    for row in reader:
      ocdid_to_name_map[row[0]] = row[1]
    reader = csv_reader('https://raw.github.com/opencivicdata/ocd-division-ids/master/identifiers/country-ca/ca_census_subdivisions.csv')
    next(reader)
    for row in reader:
      ocdid_to_name_map[row[0]] = row[1]
    ocdid_to_name_map['ocd-division/country:ca/province:qc'] = 'Québec'

  codes = province_and_territory_codes()
  ocd_id_to_code_map = {v: k for k, v in codes.items()}

  expected = {}

  sections = division_id.split('/')
  ocd_type, ocd_type_id = sections[-1].split(':')

  # Determine the module name, name and classification.
  if ocd_type == 'country':
    expected['module_name'] = 'ca'
    expected['name'] = 'Parliament of Canada'
  elif ocd_type in ('province', 'territory'):
    pattern = 'ca_%s_municipalities' if aggregation else 'ca_%s'
    expected['module_name'] = pattern % ocd_type_id
    if aggregation:
      expected['name'] = '%s Municipalities' % ocdid_to_name_map[division_id]
    elif ocd_type_id in ('nl', 'ns'):
      expected['name'] = '%s House of Assembly' % ocdid_to_name_map[division_id]
    elif ocd_type_id == 'qc':
      expected['name'] = 'Assemblée nationale du Québec'
    else:
      expected['name'] = 'Legislative Assembly of %s' % ocdid_to_name_map[division_id]
  elif ocd_type == 'cd':
    province_or_territory_type_id = codes[ocd_type_id[:2]].split(':')[-1]
    expected['module_name'] = 'ca_%s_%s' % (province_or_territory_type_id, slug(ocdid_to_name_map[division_id]))
    name_infix = ocdid_to_type_name_map[division_id]
    if name_infix == 'Regional municipality':
      name_infix = 'Regional'
    expected['name'] = '%s %s Council' % (ocdid_to_name_map[division_id], name_infix)
  elif ocd_type == 'csd':
    province_or_territory_type_id = codes[ocd_type_id[:2]].split(':')[-1]
    expected['module_name'] = 'ca_%s_%s' % (province_or_territory_type_id, slug(ocdid_to_name_map[division_id]))
    if ocd_type_id[:2] == '24':
      if ocdid_to_name_map[division_id][0] in ('A', 'E', 'I', 'O', 'U'):
        expected['name'] = "Conseil municipal d'%s" % ocdid_to_name_map[division_id]
      else:
        expected['name'] = "Conseil municipal de %s" % ocdid_to_name_map[division_id]
    else:
      name_infix = ocdid_to_type_name_map[division_id]
      if name_infix in ('Municipality', 'Specialized municipality'):
        name_infix = 'Municipal'
      elif name_infix == 'District municipality':
        name_infix = 'District'
      elif name_infix == 'Regional municipality':
        name_infix = 'Regional'
      expected['name'] = '%s %s Council' % (ocdid_to_name_map[division_id], name_infix)
  elif ocd_type == 'arrondissement':
    census_subdivision_type_id = sections[-2].split(':')[-1]
    province_or_territory_type_id = province_and_territory_codes[census_subdivision_type_id[:2]].split(':')[-1]
    expected['module_name'] = 'ca_%s_%s_%s' % (province_or_territory_type_id, slug(ocdid_to_name_map['/'.join(sections[:-1])]), slug(ocdid_to_name_map[division_id]))
    if ocdid_to_name_map[division_id][0] in ('A', 'E', 'I', 'O', 'U'):
      expected['name'] = "Conseil d'arrondissement d'%s" % ocdid_to_name_map[division_id]
    elif ocdid_to_name_map[division_id][:3] == 'Le ':
      expected['name'] = "Conseil d'arrondissement du %s" % ocdid_to_name_map[division_id][3:]
    else:
      expected['name'] = "Conseil d'arrondissement de %s" % ocdid_to_name_map[division_id]
  else:
    raise Exception('%s: Unrecognized OCD type %s' % (division_id, ocd_type))

  # Determine the class name.
  class_name_parts = re.split('[ -]', re.sub("[—–]", '-', re.sub("['.]", '', ocdid_to_name_map[division_id])))
  expected['class_name'] = unidecode(text_type(''.join(word if re.match('[A-Z]', word) else word.capitalize() for word in class_name_parts)))
  if aggregation:
    expected['class_name'] += 'Municipalities'

  # Determine the url.
  expected['url'] = ''
  if urls_memo.get(division_id):
    expected['url'] = urls_memo[division_id]

  # Determine the division name.
  expected['division_name'] = ocdid_to_name_map[division_id]

  return expected


@task
def urls():
  for module_name in os.listdir('.'):
    if os.path.isdir(module_name) and module_name not in ('.git', '_cache', '_data', '__pycache__'):
      module = importlib.import_module('%s.people' % module_name)
      if module.__dict__.get('COUNCIL_PAGE'):
        print('%-60s %s' % (module_name, module.__dict__['COUNCIL_PAGE']))
      else:
        print('%-60s COUNCIL_PAGE not defined' % module_name)


@task
def tidy():
  # Map OCD identifiers to styles of address.
  leader_styles = {}
  member_styles = {}
  reader = csv_reader('https://docs.google.com/spreadsheet/pub?key=0AtzgYYy0ZABtdFJrVTdaV1h5XzRpTkxBdVROX3FNelE&single=true&gid=0&output=csv')
  next(reader)
  for row in reader:
    key = row[0]
    leader_styles[key] = row[2]
    member_styles[key] = row[3]
  reader = csv_reader('https://docs.google.com/spreadsheet/pub?key=0AtzgYYy0ZABtdFJrVTdaV1h5XzRpTkxBdVROX3FNelE&single=true&gid=1&output=csv')
  next(reader)
  for row in reader:
    key = row[0]
    leader_styles[key] = row[2]
    member_styles[key] = row[3]

  codes = province_and_territory_codes()

  for module_name in os.listdir('.'):
    division_ids = set()
    jurisdiction_ids = set()

    if os.path.isdir(module_name) and module_name not in ('.git', '_cache', '_data', '__pycache__') and not module_name.endswith('_candidates'):
      module = importlib.import_module(module_name)
      for obj in module.__dict__.values():
        division_id = getattr(obj, 'division_id', None)
        if division_id:  # We've found the module.
          jurisdiction_id = obj.jurisdiction_id

          # Ensure division_id is unique.
          if division_id in division_ids:
            raise Exception('%s: Duplicate division_id %s' % (module_name, division_id))
          else:
            division_ids.add(division_id)

          # Ensure jurisdiction_id is unique.
          if jurisdiction_id in jurisdiction_ids:
            raise Exception('%s: Duplicate jurisdiction_id %s' % (module_name, jurisdiction_id))
          else:
            jurisdiction_ids.add(jurisdiction_id)

          expected = get_definition(division_id, bool(module_name.endswith('_municipalities')))

          class_name = obj.__name__
          division_name = getattr(obj, 'division_name', None)
          name = getattr(obj, 'name', None)
          url = getattr(obj, 'url', None)
          classification = getattr(obj, 'classification', None)

          # Ensure presence of url and styles of address.
          if not member_styles.get(division_id):
            print('%-60s No member style of address: %s' % (module_name, division_id))
          if not leader_styles.get(division_id):
            print('%-60s No leader style of address: %s' % (module_name, division_id))
          if url and not expected['url']:
            parsed = urlsplit(url)
            if parsed.scheme not in ('http', 'https') or parsed.path or parsed.query or parsed.fragment:
              print('%-60s Check: %s' % (module_name, url))

          # Warn if the name or classification may be incorrect.
          if name != expected['name']:
            print('%-60s Expected %s' % (name, expected['name']))
          if classification != 'legislature':
            print('%-60s Expected legislature' % classification)

          # Name the classes correctly.
          if class_name != expected['class_name']:
            # @note This for-loop will only run if the class name in __init__.py is incorrect.
            for basename in os.listdir(module_name):
              if basename.endswith('.py'):
                with codecs.open(os.path.join(module_name, basename), 'r', 'utf8') as f:
                  content = f.read()
                with codecs.open(os.path.join(module_name, basename), 'w', 'utf8') as f:
                  content = content.replace(class_name + '(', expected['class_name'] + '(')
                  f.write(content)

          # Set the division_name and url appropriately.
          if division_name != expected['division_name'] or (expected['url'] and url != expected['url']):
           with codecs.open(os.path.join(module_name, '__init__.py'), 'r', 'utf8') as f:
              content = f.read()
           with codecs.open(os.path.join(module_name, '__init__.py'), 'w', 'utf8') as f:
              if division_name != expected['division_name']:
                content = content.replace('= ' + division_name, '= ' + expected['division_name'])
              if expected['url'] and url != expected['url']:
                content = content.replace(url, expected['url'])
              f.write(content)

          # Name the module correctly.
          if module_name != expected['module_name']:
            print('%-60s Expected %s' % (module_name, expected['module_name']))


@task
def sources():
  for module_name in os.listdir('.'):
    if os.path.isdir(module_name) and module_name not in ('.git', '_cache', '_data', '__pycache__'):
      path = os.path.join(module_name, 'people.py')
      with codecs.open(path, 'r', 'utf-8') as f:
        content = f.read()
        if content.count('add_source') < content.count('lxmlize') - 1:  # exclude the import
          print('Add source? %s' % path)
