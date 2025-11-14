# -*- encoding: utf-8 -*-
{
	'name': 'Reporte RESULTADO POR FUNCION',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it','account_bc_report'],
	'version': '1.0',
	'description':"""
	Reporte Resultado por Funcion
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/function_result.xml',
			'wizards/function_result_wizard.xml'
			],
	'installable': True
}