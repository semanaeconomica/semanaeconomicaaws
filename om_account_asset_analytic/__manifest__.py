# -*- encoding: utf-8 -*-
{
	'name': 'Depreciation Assets Advance',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['om_account_asset'],
	'version': '1.0',
	'description':"""
	- Nueva forma de generar asientos de depreciacion en base a ctas analiticas.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'wizard/account_asset_depreciation_move.xml'
	],
	'installable': True
}
