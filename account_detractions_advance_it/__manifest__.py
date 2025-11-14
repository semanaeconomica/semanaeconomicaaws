# -*- encoding: utf-8 -*-
{
	'name': 'Detracciones Avanzadas',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_invoice_detracciones_it'],
	'version': '1.0',
	'description':"""
	Generar Detracciones en Facturas de Clientes y Proveedores Avanzado
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/detractions_catalog_percent.xml',
		'views/res_partner.xml',
		'views/account_move.xml'
	],
	'installable': True
}
