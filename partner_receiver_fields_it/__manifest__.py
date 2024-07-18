# -*- encoding: utf-8 -*-
{
	'name': 'Campos para seguimiento de pagos',
	'category': 'base',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Campos para seguimiento de pagos
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/res_partner_view.xml'
		],
	'installable': True
}
