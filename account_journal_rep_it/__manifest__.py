# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO DIARIO',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para LIBRO DIARIO
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_journal_rep.xml',
		'views/account_journal_book.xml'
	],
	'installable': True
}
