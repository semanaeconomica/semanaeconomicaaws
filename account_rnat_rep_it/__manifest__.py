# -*- encoding: utf-8 -*-
{
	'name': 'Reporte RESULTADO POR NATURALEZA',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it','account_bc_report'],
	'version': '1.0',
	'description':"""
	Reporte Resultado por Naturaleza
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/nature_result.xml',
			'wizards/nature_result_wizard.xml'
			],
	'installable': True
}