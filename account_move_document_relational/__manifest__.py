# -*- encoding: utf-8 -*-
{
	'name': 'documentos relacionados',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','account_base_it','account_fields_it'],
	'version': '1.0',
	'description':"""
	Sub-menu con vista para documentos relacionados
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_move_document_relational.xml'
		],
	'installable': True
}
