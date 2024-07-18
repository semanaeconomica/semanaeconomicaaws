# -*- encoding: utf-8 -*-
{
	'name': 'Reporte HOJA DE TRABAJO F2',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_base_it','account_fields_it','account_report_menu_it','account_bc_report'],
	'version': '1.0',
	'description':"""
	Reporte HOJA DE TRABAJO F2
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			 'security/ir.model.access.csv',
			 'views/f2_balance.xml',
			 'views/f2_register.xml',
			 'wizards/worksheet_f2_wizard.xml'],
	'installable': True
}
