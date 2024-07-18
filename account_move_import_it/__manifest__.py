# -*- encoding: utf-8 -*-
{
	'name': 'Importador de Lineas Contables',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Modulo para importar Lineas Contables
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'views/account_move.xml',
        'wizard/import_move_line_wizard.xml',
		],
	'installable': True
}
