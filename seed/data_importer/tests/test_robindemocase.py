# !/usr/bin/env python
# encoding: utf-8
"""
:copyright (c) 2014 - 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.  # NOQA
:author
"""
import datetime
import logging

from seed.data_importer import tasks
from seed.data_importer.models import ImportFile, ImportRecord
from seed.data_importer.tests.util import (
    DataMappingBaseTestCase,
    FAKE_EXTRA_DATA,
    FAKE_MAPPINGS,
    FAKE_ROW,
)
from seed.landing.models import SEEDUser as User
from seed.lib.superperms.orgs.models import Organization, OrganizationUser
from seed.models import (
    Column,
    PropertyView,
    TaxLotState,
    TaxLotView,
    DATA_STATE_IMPORT,
    DATA_STATE_MAPPING,
    ASSESSED_RAW,
)
from seed.models import (
    Cycle,
    PropertyState,
)

logger = logging.getLogger(__name__)


class TestCaseRobinDemo(DataMappingBaseTestCase):

    def set_up(self, import_file_source_type):
        """Override the base in DataMappingBaseTestCase."""

        # default_values
        import_file_is_espm = getattr(self, 'import_file_is_espm', True)
        import_file_data_state = getattr(self, 'import_file_data_state', DATA_STATE_IMPORT)

        user = User.objects.create(username='test')
        org = Organization.objects.create()

        cycle, _ = Cycle.objects.get_or_create(
            name=u'Test Hack Cycle 2015',
            organization=org,
            start=datetime.datetime(2015, 1, 1),
            end=datetime.datetime(2015, 12, 31),
        )

        # Create an org user
        OrganizationUser.objects.create(user=user, organization=org)

        import_record_1 = ImportRecord.objects.create(
            owner=user, last_modified_by=user, super_organization=org
        )
        import_file_1 = ImportFile.objects.create(import_record=import_record_1,
                                                  cycle=cycle)

        import_record_2 = ImportRecord.objects.create(
            owner=user, last_modified_by=user, super_organization=org
        )
        import_file_2 = ImportFile.objects.create(import_record=import_record_2,
                                                  cycle=cycle)

        import_file_1.is_espm = import_file_is_espm
        import_file_1.source_type = import_file_source_type
        import_file_1.data_state = import_file_data_state
        import_file_1.save()

        import_file_2.is_espm = import_file_is_espm
        import_file_2.source_type = import_file_source_type
        import_file_2.data_state = import_file_data_state
        import_file_2.save()

        return user, org, import_file_1, import_record_1, import_file_2, import_record_2, cycle

    def setUp(self):
        property_filename = getattr(self, 'filename',
                                    'example-data-properties-V2-original-noID.xlsx')
        tax_lot_filename = getattr(self, 'filename', 'example-data-taxlots-V2-original-noID.xlsx')
        import_file_source_type = ASSESSED_RAW
        self.fake_portfolio_mappings = FAKE_MAPPINGS['portfolio']
        self.fake_taxlot_mappings = FAKE_MAPPINGS['taxlot']
        self.fake_extra_data = FAKE_EXTRA_DATA
        self.fake_row = FAKE_ROW
        selfvars = self.set_up(import_file_source_type)

        (self.user,
         self.org,
         self.import_file_property,
         self.import_record_property,
         self.import_file_tax_lot,
         self.import_record_tax_lot,
         self.cycle) = selfvars

        self.import_file_tax_lot = self.load_import_file_file(tax_lot_filename,
                                                              self.import_file_tax_lot)
        self.import_file_property = self.load_import_file_file(property_filename,
                                                               self.import_file_property)

    def test_robin_demo(self):
        """ Robin's demo files """

        tasks._save_raw_data(self.import_file_tax_lot.pk, 'fake_cache_key', 1)
        Column.create_mappings(self.fake_taxlot_mappings, self.org, self.user)
        Column.create_mappings(self.fake_portfolio_mappings, self.org, self.user)
        tasks.map_data(self.import_file_tax_lot.pk)

        # self.assertEqual(len(ps), 12)

        # Check to make sure the taxlots were imported
        ts = TaxLotState.objects.filter(
            data_state=DATA_STATE_MAPPING,
            organization=self.org,
            import_file=self.import_file_tax_lot,
        )

        ps = PropertyState.objects.filter(
            data_state=DATA_STATE_MAPPING,
            organization=self.org,
            import_file=self.import_file_property,
        )

        self.assertEqual(len(ps), 0)
        self.assertEqual(len(ts), 9)

        tasks.match_buildings(self.import_file_tax_lot.id, self.user.id)

        # Check a single case of the taxlotstate
        self.assertEqual(TaxLotState.objects.filter(address_line_1='050 Willow Ave SE').count(), 1)
        self.assertEqual(
            TaxLotView.objects.filter(state__address_line_1='050 Willow Ave SE').count(), 1)

        self.assertEqual(TaxLotView.objects.count(), 9)
        self.assertEqual(PropertyView.objects.count(), 0)

        # Import the property data
        tasks._save_raw_data(self.import_file_property.pk, 'fake_cache_key', 1)
        tasks.map_data(self.import_file_property.pk)

        ts = TaxLotState.objects.filter(
            # data_state=DATA_STATE_MAPPING,
            organization=self.org,
            import_file=self.import_file_tax_lot,
        )

        ps = PropertyState.objects.filter(
            data_state=DATA_STATE_MAPPING,
            organization=self.org,
            import_file=self.import_file_property,
        )

        self.assertEqual(len(ts), 9)
        self.assertEqual(len(ps), 12)

        tasks.match_buildings(self.import_file_property.id, self.user.id)

        ps = PropertyState.objects.filter(
            data_state=DATA_STATE_MAPPING,
            organization=self.org,
            import_file=self.import_file_property,
        )

        self.assertEqual(len(ps), 0)

        # psv = PropertyView.objects.filter(state__organization=self.org)
        # self.assertEqual(len(psv), 12)

        tlv = TaxLotView.objects.filter(state__organization=self.org)
        # self.assertEqual(len(tlv), 9)

        self.assertEqual(PropertyView.objects.filter(state__organization=self.org,
                                                     state__pm_property_id='2264').count(), 1)
        pv = PropertyView.objects.filter(state__organization=self.org,
                                         state__pm_property_id='2264').first()

        self.assertEqual(pv.state.property_name, 'University Inn')
        self.assertEqual(pv.state.address_line_1, '50 Willow Ave SE')

        self.assertEqual(TaxLotView.objects.filter(state__organization=self.org,
                                                   state__jurisdiction_tax_lot_id='13334485').count(),
                         1)
        tlv = TaxLotView.objects.filter(state__organization=self.org,
                                        state__jurisdiction_tax_lot_id='13334485').first()
        self.assertEqual(tlv.state.address_line_1, '93029 Wellington Blvd')
