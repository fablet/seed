# !/usr/bin/env python
# encoding: utf-8
"""
:copyright (c) 2014 - 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.  # NOQA
:author
"""
import logging
from IPython import embed

from seed.data_importer import tasks
from seed.data_importer.tests.util import (
    DataMappingBaseTestCase,
    FAKE_EXTRA_DATA,
    FAKE_MAPPINGS,
    FAKE_ROW,
)
from seed.models import (
    Column,
    Property,
    PropertyState,
    PropertyView,
    TaxLot,
    TaxLotState,
    TaxLotProperty,
    TaxLotView,
    DATA_STATE_MAPPING,
    ASSESSED_RAW,
)

logger = logging.getLogger(__name__)


class TestCaseA(DataMappingBaseTestCase):

    def setUp(self):
        filename = getattr(self, 'filename', 'example-data-properties.xlsx')
        import_file_source_type = ASSESSED_RAW
        self.fake_mappings = FAKE_MAPPINGS['portfolio']
        self.fake_extra_data = FAKE_EXTRA_DATA
        self.fake_row = FAKE_ROW
        selfvars = self.set_up(import_file_source_type)
        self.user, self.org, self.import_file, self.import_record, self.cycle = selfvars
        self.import_file = self.load_import_file_file(filename, self.import_file)

    def test_import_file(self):
        tasks._save_raw_data(self.import_file.pk, 'fake_cache_key', 1)
        Column.create_mappings(self.fake_mappings, self.org, self.user)
        tasks.map_data(self.import_file.pk)

        ps = PropertyState.objects.filter(pm_property_id='2264').first()
        ps.promote(self.cycle)

        # should only be 11 unmatched_properties because one was promoted.
        ps = self.import_file.find_unmatched_property_states()
        self.assertEqual(len(ps), 11)

    def test_match_buildings(self):
        """ case A (one property <-> one tax lot) """
        tasks._save_raw_data(self.import_file.pk, 'fake_cache_key', 1)
        Column.create_mappings(self.fake_mappings, self.org, self.user)
        tasks.map_data(self.import_file.pk)

        # Check to make sure all the properties imported
        ps = PropertyState.objects.filter(
            data_state=DATA_STATE_MAPPING,
            organization=self.org,
            import_file=self.import_file,
        )
        self.assertEqual(len(ps), 12)

        # Check to make sure the taxlots were imported
        ts = TaxLotState.objects.filter(
            data_state=DATA_STATE_MAPPING,
            organization=self.org,
            import_file=self.import_file,
        )
        # self.assertEqual(len(ts), 10)  # 10 unique taxlots after duplicates and delimeters

        # Check a single case of the taxlotstate
        ts = TaxLotState.objects.filter(jurisdiction_tax_lot_id='1552813').first()
        self.assertEqual(ts.jurisdiction_tax_lot_id, '1552813')
        self.assertEqual(ts.address_line_1, None)
        self.assertEqual(ts.extra_data["extra_data_2"], 1)

        # Check a single case of the propertystate
        ps = PropertyState.objects.filter(pm_property_id='2264')
        self.assertEqual(len(ps), 1)
        ps = ps.first()
        self.assertEqual(ps.pm_property_id, '2264')
        self.assertEqual(ps.address_line_1, '50 Willow Ave SE')
        self.assertEqual(ps.extra_data["extra_data_1"], 'a')
        self.assertEqual('extra_data_2' in ps.extra_data.keys(), False)

        # verify that the lot_number has the tax_lot information. For this case it is one-to-one
        self.assertEqual(ps.lot_number, ts.jurisdiction_tax_lot_id)

        tasks.match_buildings(self.import_file.id, self.user.id)

        self.assertEqual(TaxLot.objects.count(), 10)
        self.assertEqual(Property.objects.count(), 10)  # Two properties match on custom_id_1 for 7 and 9

        qry = PropertyView.objects.filter(state__custom_id_1='7')
        self.assertEqual(qry.count(), 1)

        state = qry.first().state

        self.assertEqual(state.address_line_1, "20 Tenth Street")
        self.assertEqual(state.property_name, "Grange Hall")
