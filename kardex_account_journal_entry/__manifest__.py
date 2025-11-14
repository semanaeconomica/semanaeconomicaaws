# -*- encoding: utf-8 -*-
{
	'name': 'Analisis de Consumo',
	'category': 'stock',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','kardex_valorado_it_multi','kardex_fields_it'],
	'version': '1.0',
	'description':"""
	- Reporte de Analisis de Consumo
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'SQL.sql',
		'security/ir.model.access.csv',
		'wizards/consumption_analysis_wizard.xml',
		'wizards/costs_sales_analysis_wizard.xml',
		'views/consumption_analysis_book.xml',
		'views/costs_sales_analysis_book.xml'
	],
	'installable': True
}
