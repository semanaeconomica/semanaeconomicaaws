# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Entregas a Rendir IT',
	'category': 'Accounting',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','report_tools','account_statement_payment'],
	'version': '1.0',
	'description':"""
	- Reporte Entregas a Rendir Calquipa IT
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_bank_statement.xml',
		'wizard/report_render_wizard.xml'
	],
	'installable': True
}