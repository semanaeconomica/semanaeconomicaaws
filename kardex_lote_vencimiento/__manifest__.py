# -*- encoding: utf-8 -*-
{
	'name': 'Mantenimiento',
	'category': 'maintenance',
	'author': 'ITGRUPO',
	'depends': ['stock'],
	'version': '1.0',
	'description':"""
	Modulo para crear tabla de Parametros en Ventas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'security/ir.model.access.csv',
			'views/sale_main_parameter.xml',
			],
	'installable': True
}
