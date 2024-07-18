# -*- encoding: utf-8 -*-
{
	'name': 'Reporte SITUACION FINANCIERA',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it','account_bc_report'],
	'version': '1.0',
	'description':"""
	Reporte Situacion Financiera
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/financial_situation.xml',
			'wizards/financial_situation_wizard.xml'
			],
	'installable': True
}