# -*- encoding: utf-8 -*-
{
	'name': 'Reporte FLUJO EFECTIVO',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it','account_bc_report'],
	'version': '1.0',
	'description':"""
	Reporte de Flujo de Efectivo
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/efective_flow.xml',
			'wizards/efective_flow_wizard.xml'
			],
	'installable': True
}