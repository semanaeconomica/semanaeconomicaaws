# -*- encoding: utf-8 -*-
{
	'name': 'Account Journal Sequence',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_base_it','account'],
	'version': '1.0',
	'description':"""
	Generacion de Secuencias para Diarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/account_journal.xml',
			'wizards/account_sequence_journal_wizard.xml',
			'wizards/sequence_wizard.xml'
			],
	'installable': True
}
