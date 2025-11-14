# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Flujo de Caja Proyectado',
	'category': 'account',
	'author': 'ITGRUPO-SEMANA ECONOMICA',
	'depends': ['account_cash_flow_rep','account_report_menu_it','account_balance_semaeco_doc_rep_it'],
	'version': '1.0',
	'description':"""
	- Reporte Flujo de Caja Proyectado
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'SQL.sql',
		'views/account_projected_cash_flow_book.xml',
		'views/account_data_projected_cash_flow.xml',
		'wizard/account_projected_cash_flow_rep.xml'
	],
	'installable': True
}