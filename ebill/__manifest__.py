# -*- encoding: utf-8 -*-
{
	'name': 'Ebill',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','base','product','account_base_it','account_fields_it','l10n_pe'],
	'version': '1.0',
	'description':"""
	Modulo de Facturacion Electronica
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'security/ir.model.access.csv',
			'data/res_country_state.xml',
			#'data/updates.xml',
			'views/res_country_state.xml',
			'views/einvoice_catalog_01.xml',
			'views/einvoice_catalog_payment.xml',
			'views/account_tax.xml',
			'views/account_move.xml',
			'views/main_parameter.xml',
			'views/res_partner.xml',
			'views/einvoice.xml',
			'views/einvoice_line.xml',
			'views/res_currency.xml'
			],
	'installable': True
}
