# -*- encoding: utf-8 -*-
{
	'name': 'Cargar Plan Contable LC',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','account_journal_sequence'],
	'version': '1.0',
	'description':"""
		Cargar Plan Contable para LC13
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'sql_update_main_parameter.sql',
		'wizard/upload_chart_account_it.xml'
	],
	'installable': True
}
