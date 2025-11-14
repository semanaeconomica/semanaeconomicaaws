# -*- encoding: utf-8 -*-
{
	'name': 'Kardex Fields',
	'category': 'Operations/Inventory',
	'author': 'ITGRUPO-OWM',
	'depends': ['analytic','stock'],
	'version': '1.0',
	'description':"""
	- Agregar campos para Cuentas Analiticas en Albaranes
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/stock_picking.xml','assets.xml'
		],
	'installable': True
}
