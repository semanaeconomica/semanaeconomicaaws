# -*- encoding: utf-8 -*-
{
	'name': 'Importador de Asientos Contables IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Importador de Asientos Contables
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/attachment_sample.xml',
		'wizard/import_journal_entry_it.xml',
		'views/delete_journal_entry_import.xml'
		],
	'installable': True
}
