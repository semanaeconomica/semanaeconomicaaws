# -*- encoding: utf-8 -*-
{
	'name': 'Importar inventario inicial',
	'category': 'stock',
	'author': 'ITGRUPO',
	'depends': ['stock', 'kardex_fisico_it', 'popup_it'],
	'version': '1.0.0',
	'description':"""
	IMPORTA EL INVENTARIO INICIAL SIN LOTES
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'security/ir.model.access.csv',
			'import_rest_inv_view.xml'
			],
	'installable': True
}