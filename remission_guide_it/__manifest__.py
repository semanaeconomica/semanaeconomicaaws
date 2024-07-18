# -*- encoding: utf-8 -*-
{
	'name': 'Guias Electronicas IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['ebill','stock_picking_note','popup_it'],
	'version': '1.0',
	'description':"""
	Modulo para imprimir CPE en Facturas de Clientes
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/main_parameter.xml',
		'views/stock_picking.xml',
		'wizard/view_remission_guide_wizard.xml',
		],
	'css':[
		'static/src/css/styles.css',
		],
	'installable': True
}
