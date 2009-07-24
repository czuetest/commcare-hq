import unittest
from xformmanager.tests.util import *
from xformmanager.models import *
from xformmanager.storageutility import StorageUtility
from organization.models import Domain
#from django.test import TestCase

class CaseTestCase(unittest.TestCase):
    
    def setUp(self):
        # clean up, in case some other tests left some straggling
        # form data.
        su = StorageUtility()
        su.clear()
        # register some schemas
        create_xsd_and_populate("data/pf_followup.xsd", "data/pf_followup_1.xml")
        for i in range(2, 6):
            populate("data/pf_followup_%s.xml" % i)
        
        create_xsd_and_populate("data/pf_new_reg.xsd", "data/pf_new_reg_1.xml")
        create_xsd_and_populate("data/pf_ref_completed.xsd", "data/pf_ref_completed_1.xml")
        
        # get the three forms
        self.reg_form = FormDefModel.objects.get(form_name="schema_pathfinder_pathfinder_cc_registration_0_0_2")
        self.follow_form = FormDefModel.objects.get(form_name="schema_pathfinder_pathfinder_cc_follow_0_0_2")
        self.close_form = FormDefModel.objects.get(form_name="schema_pathfinder_pathfinder_cc_resolution_0_0_2")
        
        # make some objects for these to build our case
        self.reg_fid = FormIdentifier.objects.create(form=self.reg_form, identity_column="meta_username")
        self.follow_fid = FormIdentifier.objects.create(form=self.follow_form, identity_column="meta_username", 
                                                        sorting_column="meta_timeend", sort_descending=True)
        self.close_fid = FormIdentifier.objects.create(form=self.close_form, identity_column="meta_username")
        
        pf_domain = Domain.objects.all()[0]
        self.pf_case = Case.objects.create(name="pathfinder cases", domain=pf_domain)
        
        self.reg_cfi = CaseFormIdentifier.objects.create(form_identifier=self.reg_fid, case=self.pf_case, sequence_id=1)
        self.follow_cfi = CaseFormIdentifier.objects.create(form_identifier=self.follow_fid, case=self.pf_case, sequence_id=2)
        self.close_cfi = CaseFormIdentifier.objects.create(form_identifier=self.close_fid, case=self.pf_case, sequence_id=3)
        
    def testFormIdentifier(self):
        uniques = self.reg_fid.get_uniques()
        self.assertEqual(1, len(uniques))
        self.assertEqual("mary", uniques[0])
        uniques = self.follow_fid.get_uniques()
        self.assertEqual(2, len(uniques))
        self.assertEqual("demo_user", uniques[0])
        self.assertEqual("mary", uniques[1])
        uniques = self.close_fid.get_uniques()
        self.assertEqual(1, len(uniques))
        self.assertEqual("demo_user", uniques[0])
        
    def testGetFormUtilities(self):
        pf_forms = self.pf_case.forms
        self.assertEqual(3, len(pf_forms))
        self.assertEqual(self.reg_form, pf_forms[0])
        self.assertEqual(self.follow_form, pf_forms[1])
        self.assertEqual(self.close_form, pf_forms[2])
        
        pf_form_ids = self.pf_case.form_identifiers
        self.assertEqual(3, len(pf_form_ids))
        self.assertEqual(self.reg_fid, pf_form_ids[0])
        self.assertEqual(self.follow_fid, pf_form_ids[1])
        self.assertEqual(self.close_fid, pf_form_ids[2])
        
        # change around the sequence ids and make sure they come back in the right order
        self.follow_cfi.sequence_id = 4
        self.follow_cfi.save()
        
        pf_forms = self.pf_case.forms
        self.assertEqual(3, len(pf_forms))
        self.assertEqual(self.reg_form, pf_forms[0])
        self.assertEqual(self.close_form, pf_forms[1])
        self.assertEqual(self.follow_form, pf_forms[2])
        
        pf_form_ids = self.pf_case.form_identifiers
        self.assertEqual(3, len(pf_form_ids))
        self.assertEqual(self.reg_fid, pf_form_ids[0])
        self.assertEqual(self.close_fid, pf_form_ids[1])
        self.assertEqual(self.follow_fid, pf_form_ids[2])
          
    def testGetUniqueIds(self):
        uniques = self.pf_case.get_unique_ids()
        self.assertEqual(2, len(uniques))
        # for now, we don't know what order these will come back in
        if uniques[0] == "mary":
            self.assertEqual("demo_user", uniques[1])
        elif uniques[0] == "demo_user":
            self.assertEqual("mary", uniques[1])
        else:
            self.fail("Get uniques returned wrong first value: %s" % uniques[0])
        
    def testGetColumnNames(self):
        reg_cols = self.reg_form.get_column_names()
        follow_cols = self.follow_form.get_column_names()
        close_cols = self.close_form.get_column_names()
        total_cols = len(reg_cols) + len(follow_cols) + len(close_cols)
        case_cols = self.pf_case.get_column_names()
        self.assertEqual(total_cols, len(case_cols))
        
        # walk through the list of columns in order and
        # ensure that each table's columns match up. 
        count = 0
        for col in reg_cols:
            self.assertTrue(col in case_cols[count])
            count += 1
        
        for col in follow_cols:
            self.assertTrue(col in case_cols[count])
            count += 1
        
        for col in close_cols:
            self.assertTrue(col in case_cols[count])
            count += 1
    
    def testGetDataFromFormIdentifier(self):
        followup_data = self.follow_fid.get_data_maps()
        self.assertEqual(2, len(followup_data))
        self.assertEqual(3, len(followup_data["demo_user"]))
        self.assertEqual(2, len(followup_data["mary"]))
        for id, list in followup_data.items():
            dict = list[0]
            self.assertEqual(id, dict[self.follow_fid.identity_column])  
            # add the sorting checks based on the knowledge of the form.
            # This is done by manually setting the device ids in the forms
            if id == "demo_user":
                self.assertEqual("device3", dict["meta_deviceid"])
            elif id == "mary":
                self.assertEqual("device5", dict["meta_deviceid"])
            else:
                self.fail("unexpected identity: %s" % id)
        
        # change the sort order and make sure it works
        self.follow_fid.sort_descending = False
        self.follow_fid.save()
        followup_data = self.follow_fid.get_data_maps()
        self.assertEqual(2, len(followup_data))
        self.assertEqual(3, len(followup_data["demo_user"]))
        self.assertEqual(2, len(followup_data["mary"]))
        for id, list in followup_data.items():
            dict = list[0]
            self.assertEqual(id, dict[self.follow_fid.identity_column])  
            if id == "demo_user":
                self.assertEqual("device1", dict["meta_deviceid"])
            elif id == "mary":
                self.assertEqual("device4", dict["meta_deviceid"])
            else:
                self.fail("unexpected identity: %s" % id)
        
        # change the sorting column and do it one more time
        self.follow_fid.sorting_column = "meta_timestart"
        self.follow_fid.save()
        followup_data = self.follow_fid.get_data_maps()
        self.assertEqual(2, len(followup_data))
        self.assertEqual(3, len(followup_data["demo_user"]))
        self.assertEqual(2, len(followup_data["mary"]))
        for id, list in followup_data.items():
            dict = list[0]
            self.assertEqual(id, dict[self.follow_fid.identity_column])  
            if id == "demo_user":
                self.assertEqual("device3", dict["meta_deviceid"])
                self.assertEqual(3, len(list))
            elif id == "mary":
                self.assertEqual("device5", dict["meta_deviceid"])
                self.assertEqual(2, len(list))
            else:
                self.fail("unexpected identity: %s" % id)
        
    def testGetTopmostData(self):
        data = self.pf_case.get_topmost_data_maps()
        self.assertEqual(2, len(data))
        for id, col_map in data.items():
            if id == "demo_user":
                self.assertEqual("device3", 
                                 col_map["meta_deviceid_%s" % self.follow_cfi.sequence_id])
                # demo_user has a close form but no reg
                # the id below is copied from the xml form
                self.assertEqual("7WM8SPBUWGXTDRO4TAJVR6MA0",
                                 col_map["meta_uid_%s" % self.close_cfi.sequence_id])
                self.assertEqual(None,
                                 col_map["meta_uid_%s" % self.reg_cfi.sequence_id])
            elif id == "mary":
                self.assertEqual("device5", 
                                 col_map["meta_deviceid_%s" % self.follow_cfi.sequence_id])
                # mary has a reg, but no close form
                # the id below is copied from the xml form
                self.assertEqual("NFLFYINTDW16XPMOY0QXVXSH1",
                                 col_map["meta_uid_%s" % self.reg_cfi.sequence_id])
                self.assertEqual(None,
                                 col_map["meta_uid_%s" % self.close_cfi.sequence_id])
            else:
                self.fail("unexpected identity: %s" % id)
                
                
    def testGetCaseData(self):
        data = self.pf_case.get_data_for_case("demo_user")
        self.assertEqual(3, len(data))
        self.assertEqual(0, len(data[self.reg_fid]))
        self.assertEqual(3, len(data[self.follow_fid]))
        self.assertEqual(1, len(data[self.close_fid]))
        data = self.pf_case.get_data_for_case("mary")
        self.assertEqual(3, len(data))
        self.assertEqual(1, len(data[self.reg_fid]))
        self.assertEqual(2, len(data[self.follow_fid]))
        self.assertEqual(0, len(data[self.close_fid]))
    
    def testGetAllData(self):
        all_data = self.pf_case.get_all_data_maps()
        self.assertEqual(2, len(all_data))
        data = all_data["demo_user"]
        self.assertEqual(3, len(data))
        self.assertEqual(0, len(data[self.reg_fid]))
        self.assertEqual(3, len(data[self.follow_fid]))
        self.assertEqual("device3", 
                         data[self.follow_fid][0]["meta_deviceid"])
        self.assertEqual("device2", 
                         data[self.follow_fid][1]["meta_deviceid"])
        self.assertEqual("device1", 
                         data[self.follow_fid][2]["meta_deviceid"])
        self.assertEqual(1, len(data[self.close_fid]))
        data = all_data["mary"]
        self.assertEqual(3, len(data))
        self.assertEqual(1, len(data[self.reg_fid]))
        self.assertEqual(2, len(data[self.follow_fid]))
        self.assertEqual("device5", 
                         data[self.follow_fid][0]["meta_deviceid"])
        self.assertEqual("device4", 
                         data[self.follow_fid][1]["meta_deviceid"])
        self.assertEqual(0, len(data[self.close_fid]))
        