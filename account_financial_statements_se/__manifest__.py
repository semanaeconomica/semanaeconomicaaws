# -*- encoding: utf-8 -*-
{
	'name': 'ESTADOS FINANCIEROS SE',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it','mail','account_budget_it','bi_import_chart_of_accounts'],
	'version': '1.0',
	'description':"""
		- ESTADOS FINANCIEROS SE
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'security/security.xml',
		'data/account_patrimony_type.xml',
		'data/account_patrimony_table.xml',
		'views/menu_views.xml',
		'views/account_patrimony_table.xml',
		'views/account_account_type.xml',
		'views/account_move.xml',
		'views/account_journal_ingreso_se_book.xml',
		'wizards/account_journal_ingreso_se_rep.xml',
		'wizards/account_ecpn_rep.xml'
	],
	'installable': True
}