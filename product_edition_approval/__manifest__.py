# -*- encoding: utf-8 -*-
{
	'name': 'Aprobaciones al Maestro de ediciones',
	'category': 'product',
	'author': 'ITGRUPO',
	'depends': ['product_edition_it'],
	'version': '1.0',
	'description':"""
		Añade la capacidad de aprobacipones a las ediciones
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/product_editon_approval_view.xml',	
		'views/product_edition_it_view.xml'
	],
	'installable': True
}
