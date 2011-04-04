#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

# UNICEF SD - 2008 Country Forecasting Data.xls
cf_2008_products = [u'dtp-hepbhib-1', u'measles', u'mmr-1']
cf_2008_unmatched_products = [u'Rotavirus', u'DTP-Hib (liq)', u'Meningitis', u'Pneumo-7', u'DPT-Hib', u'DTP-Hib (lyoph)', u'Pneumo', u'Hep B', u'mOPV1']
cf_2008_matched_groups = [u'OPV', u'Influenza', u'DTP-HepB', u'BCG', u'MMR', u'DTP-Hib', u'Hib', u'YF', u'MR', u'TT', u'DT', u'DTP', u'Td', u'DTP-HepB/Hib']

# UNICEF SD - 2009 Country Forecasting Data.xls
cf_2009_products = [u'mr-10', u'hepb-6', u'dtp-10', u'hepb-1', u'bcg-20', u'mopv3-20', u'hepb-2', u'yf-5', u'tt-10', u'yf-1', u'mmr-1', u'yf-20', u'hib-1-lph', u'dtp-hepbhib-2', u'mopv1-20', u'dtp-20', u'mmr-10', u'cholera', u'dtp-hib-1-lph', u'td-10', u'tt-20', u'hepb-10', u'dt-10', u'hib-1-lqd', u'yf-10']
cf_2009_unmatched_products = [u'Hepatitis A vaccine ', u'Rota-1 (lph)', u'DTP-Hib-10 (lqd)', u'Meningitis AM-BC', u'DTP-HepB-2(lqd)', u'OPV-10', u'Pneumo-1 (7val)', u'DTP-HepB-Hib-10(lqd)', u'Pneumo-2 (10 val)', u'DTP-HepB-10(lqd)', u'HepB-1**', u'Meningitis-10', u'Measles-10', u'Hep B', u'Meningococcal A', u'DTP-HepB-Hib-1(lqd)', u'OPV-20']
cf_2009_matched_groups = [u'DTP-HepB', u'DTP', u'Td', u'MR', u'MMR']

# UNICEF SD - 2010 Country Forecasting Data.xls
cf_2010_products = [u'mr-10', u'hepb-6', u'dtp-10', u'hepb-1', u'bcg-20', u'mopv3-20', u'yf-5', u'tt-10', u'mmr-1', u'yf-20', u'hib-1-lph', u'dtp-hepbhib-2', u'mopv1-20', u'dtp-20', u'mmr-10', u'hepb-2', u'dtp-hib-1-lph', u'td-10', u'tt-20', u'hepb-10', u'dt-10', u'hib-1-lqd', u'yf-10']
cf_2010_unmatched_products = [u'DTP-Hib-10 (lqd)', u'OPV-10', u'Pneumo-1 (7val)', u'DPT-Hib', u'Rota-1 (lqd)', u'DTP-HepB-Hib-10(lqd)', u'DTP-HepB-10(lqd)', u'Pneumo-2 (10 val)', u'bOPV', u'Meningitis-10', u'Measles-10', u'tOPV', u'Hep B', u'Meningococcal A', u'DTP-HepB-Hib-1(lqd)', u'mOPV1', u'OPV-20']
cf_2010_matched_groups = [u'OPV', u'DTP', u'DTP-HepB/Hib', u'MMR']

cf_products = [u'mr-10', u'hepb-6', u'dtp-10', u'hepb-1', u'bcg-20', u'mopv3-20', u'hepb-2', u'yf-5', u'tt-10', u'yf-1', u'mmr-1', u'yf-20', u'cholera', u'dtp-hepbhib-1', u'hib-1-lph', u'dtp-hepbhib-2', u'dtp-hib-1-lph', u'dtp-20', u'mmr-10', u'measles', u'mopv1-20', u'td-10', u'tt-20', u'hepb-10', u'dt-10', u'hib-1-lqd', u'yf-10']
cf_unmatched_products = [u'Hepatitis A vaccine ', u'Rotavirus', u'DTP-Hib (liq)', u'Pneumo-7', u'bOPV', u'DTP-Hib (lyoph)', u'DTP-HepB-Hib-1(lqd)', u'Meningitis', u'DTP-HepB-2(lqd)', u'HepB-1**', u'Pneumo-1 (7val)', u'Meningococcal A', u'Rota-1 (lqd)', u'Measles-10', u'OPV-20', u'Rota-1 (lph)', u'Meningitis-10', u'DTP-HepB-10(lqd)', u'Hep B', u'mOPV1', u'Meningitis AM-BC', u'DTP-Hib-10 (lqd)', u'OPV-10', u'DPT-Hib', u'DTP-HepB-Hib-10(lqd)', u'Pneumo-2 (10 val)', u'Pneumo', u'tOPV']
cf_matched_groups = [u'OPV', u'Influenza', u'DTP-HepB', u'BCG', u'Td', u'MMR', u'DTP-Hib', u'Hib', u'DTP', u'MR', u'DT', u'YF', u'TT', u'DTP-HepB/Hib']


# UNICEF SD - 2008 YE Allocations + Country Office Forecasts 2008.xls
a_2008_products = [u'mr-10', u'hepb-6', u'dtp-hepb-10', u'dtp-10', u'hepb-1', u'bcg-20', u'mopv3-20', u'dtp-hepb-2', u'yf-5', u'mea-1', u'tt-10', u'dtp-hib-10', u'mmr-1', u'yf-20', u'dtp-hepbhib-1', u'dtp-hepbhib-2', u'dtp-hib-1-lph', u'dtp-20', u'mmr-10', u'hepb-2', u'mopv1-20', u'td-10', u'mening-acyw135-10', u'tt-20', u'mea-10', u'hepb-10', u'hib-1', u'dt-10', u'yf-10']
a_2008_unmatched_products = [u'Meningitis-50', u'Rotavirus-10', u'DTP-Hib-10 (lqd)', u'OPV-10', u'Pneumo-10', u'Meningitis-10', u'Pneumo-1', u'DTP-Hib-1', u'Typhoid-1', u'DTP+Hib-10 (lph)', u'OPV-20']
a_2008_matched_groups = []

# UNICEF SD - 2009 YE Allocations + Country Office Forecasts 2009.xls
a_2009_products = [u'mr-10', u'hepb-6', u'dtp-hepb-10', u'dtp-10', u'hepb-1', u'bcg-20', u'mopv3-20', u'dtp-hepb-2', u'hepb-2', u'yf-5', u'mea-1', u'tt-10', u'yf-1', u'ipv-10', u'mmr-1', u'yf-20', u'topv-20', u'dtp-hepbhib-1', u'dtp-hepbhib-2', u'dtp-hib-1-lph', u'dtp-20', u'mmr-10', u'bopv-20', u'mopv1-20', u'td-10', u'mening-acyw135-10', u'tt-20', u'mea-10', u'influenza-1', u'hepb-10', u'hib-1', u'dt-10', u'yf-50', u'yf-10', u'topv-10']
a_2009_unmatched_products = [u'Meningitis-50', u'DTP-Hib-10 (lqd)', u'OPV-10', u'Meningitis-10', u'OPV-20', u'DTP-HepB-Hib-10', u'DTP+Hib-10 (lph)', u'PCV7-1']
a_2009_matched_groups = []

a_products = [u'mr-10', u'hepb-6', u'dtp-hepb-10', u'hepb-2', u'hepb-1', u'bcg-20', u'mopv3-20', u'dtp-hepb-2', u'yf-5', u'mea-1', u'tt-10', u'yf-1', u'ipv-10', u'dtp-hib-10', u'mmr-1', u'yf-20', u'topv-20', u'bopv-20', u'dtp-hepbhib-1', u'dtp-hepbhib-2', u'mopv1-20', u'dtp-20', u'mmr-10', u'dtp-10', u'dtp-hib-1-lph', u'td-10', u'mening-acyw135-10', u'tt-20', u'dt-10', u'influenza-1', u'hepb-10', u'hib-1', u'mea-10', u'yf-50', u'yf-10', u'topv-10']
a_unmatched_products = [u'Meningitis-50', u'Rotavirus-10', u'DTP-Hib-10 (lqd)', u'OPV-10', u'Pneumo-10', u'Meningitis-10', u'PCV7-1', u'Pneumo-1', u'Typhoid-1', u'DTP-HepB-Hib-10', u'DTP+Hib-10 (lph)', u'OPV-20', u'DTP-Hib-1']

unicef_products = [u'mr-10', u'hepb-6', u'dtp-hepb-10', u'hepb-2', u'hepb-1', u'bcg-20', u'bopv-20', u'mopv3-20', u'dtp-hepb-2', u'yf-5', u'mea-1', u'tt-10', u'yf-1', u'ipv-10', u'dtp-hib-10', u'mmr-1', u'yf-20', u'topv-20', u'cholera', u'dtp-hepbhib-1', u'hib-1-lph', u'dtp-hepbhib-2', u'mopv1-20', u'dtp-20', u'mmr-10', u'dtp-10', u'dtp-hib-1-lph', u'td-10', u'mening-acyw135-10', u'tt-20', u'mea-10', u'influenza-1', u'hepb-10', u'hib-1', u'dt-10', u'yf-50', u'hib-1-lqd', u'yf-10', u'topv-10', u'measles']
unicef_unmatched_products = [u'Hepatitis A vaccine ', u'Rotavirus', u'Rotavirus-10', u'DTP-Hib (liq)', u'Pneumo-7', u'Pneumo-1', u'bOPV', u'DTP-Hib (lyoph)', u'DTP-Hib-1', u'Typhoid-1', u'DTP-HepB-Hib-10', u'DTP+Hib-10 (lph)', u'DTP-HepB-Hib-1(lqd)', u'PCV7-1', u'Meningitis', u'DTP-HepB-2(lqd)', u'Pneumo-2 (10 val)', u'Pneumo-1 (7val)', u'Pneumo-10', u'Meningococcal A', u'Rota-1 (lqd)', u'Measles-10', u'OPV-20', u'Meningitis-50', u'Rota-1 (lph)', u'Meningitis-10', u'DTP-HepB-10(lqd)', u'Hep B', u'mOPV1', u'Meningitis AM-BC', u'DTP-Hib-10 (lqd)', u'OPV-10', u'DPT-Hib', u'DTP-HepB-Hib-10(lqd)', u'HepB-1**', u'Pneumo', u'tOPV']
unicef_matched_groups = [u'OPV', u'Influenza', u'DTP-HepB', u'BCG', u'Td', u'MMR', u'DTP-Hib', u'Hib', u'DTP', u'MR', u'DT', u'YF', u'TT', u'DTP-HepB/Hib']


# Chad_Stocks.xls
chad_products = []
chad_unmatched_products = [u'DTC', u'VAR', u'VPO', u'VAA', u'VAT']
chad_matched_groups = [u'BCG']

# Mali_stocks.xls
mali_products = []
mali_unmatched_products = [u'Hib_lyo', u'DTC', u'VAA', u'DTC-HepB', u'VAR', u'VPO', u'VAT']
mali_matched_groups = [u'BCG']

# Senegal_stocks.xls
senegal_products = []
senegal_unmatched_products = [u'VAR', u'DTC-HepB-Hib', u'VPO', u'VAA', u'VAT']
senegal_matched_groups = [u'BCG']

who_products = []
who_unmatched_products = [u'Hib_lyo', u'DTC', u'VAA', u'DTC-HepB', u'VAR', u'DTC-HepB-Hib', u'VPO', u'VAT']
who_matched_groups = [u'BCG']


all_products = [u'mr-10', u'hepb-6', u'dtp-hepb-10', u'hepb-2', u'hepb-1', u'bcg-20', u'bopv-20', u'mopv3-20', u'dtp-hepb-2', u'yf-5', u'mea-1', u'tt-10', u'yf-1', u'ipv-10', u'dtp-hib-10', u'mmr-1', u'yf-20', u'topv-20', u'cholera', u'dtp-hepbhib-1', u'hib-1-lph', u'dtp-hepbhib-2', u'mopv1-20', u'dtp-20', u'mmr-10', u'dtp-10', u'dtp-hib-1-lph', u'td-10', u'mening-acyw135-10', u'tt-20', u'mea-10', u'influenza-1', u'hepb-10', u'hib-1', u'dt-10', u'yf-50', u'hib-1-lqd', u'yf-10', u'topv-10', u'measles']
all_unmatched_products = [u'Hepatitis A vaccine ', u'Rotavirus', u'Rotavirus-10', u'DTP-Hib (liq)', u'Pneumo-7', u'Pneumo-1', u'VAR', u'VAA', u'bOPV', u'DTP-Hib (lyoph)', u'DTP-Hib-1', u'Typhoid-1', u'DTP-HepB-Hib-10', u'DTP+Hib-10 (lph)', u'DTP-HepB-Hib-1(lqd)', u'PCV7-1', u'Meningitis', u'DTP-HepB-2(lqd)', u'HepB-1**', u'Pneumo-1 (7val)', u'Pneumo-10', u'Meningococcal A', u'DTC', u'DTC-HepB', u'mOPV1', u'Measles-10', u'VPO', u'OPV-20', u'Meningitis-50', u'Rota-1 (lph)', u'Hib_lyo', u'VAT', u'Meningitis-10', u'DTP-HepB-10(lqd)', u'Hep B', u'DTC-HepB-Hib', u'Rota-1 (lqd)', u'Meningitis AM-BC', u'DTP-Hib-10 (lqd)', u'OPV-10', u'DPT-Hib', u'DTP-HepB-Hib-10(lqd)', u'Pneumo-2 (10 val)', u'Pneumo', u'tOPV']
all_matched_groups = [u'OPV', u'Influenza', u'DTP-HepB', u'BCG', u'MMR', u'DTP-Hib', u'Hib', u'YF', u'MR', u'TT', u'Td', u'DTP', u'DT', u'DTP-HepB/Hib']

def go():
    for v in all_unmatched_products:
        reconcile_vaccine_interactively(v)
