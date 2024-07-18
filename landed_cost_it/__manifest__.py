# -*- encoding: utf-8 -*-
{
	'name': 'Gastos Vinculados IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','stock','purchase','account_fields_it','l10n_pe_currency_rate'],
	'version': '1.0',
	'description':"""
	Gastos Vinculados Localizacion Contable 13
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/landed_cost_it.xml',
		'views/landed_invoice_book.xml',
		'views/landed_purchase_book.xml',
		'views/product_template.xml',
		'wizard/get_landed_purchases_wizard.xml',
		'wizard/get_landed_invoices_wizard.xml'
		],
	'installable': True
}