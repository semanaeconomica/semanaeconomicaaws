# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Import Partner and Update Partner in Odoo',
    'version': '13.0.0.0',
    'category' : 'Sales',
    "price": 7,
    "currency": 'EUR',
    'summary': 'Apps for import product import product template import product data import product variants import update product update product template update product data update product template import product from excel import product from xls import products data',
    'description': """
    
    from excel import partners in odoo,
   
    """,
    'author': 'BrowseInfo-ITGRUPO',
    'website': 'www.browseinfo.in',
    'depends': ['contacts','account_fields_it','popup_it'],
    'data': [
      "data/attachment_sample.xml",
	     "views/partner.xml",
             ],
	'qweb': [
		],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/5hQVhTl2Y-Y',
    "images":["static/description/Banner.png"],
}
