# -*- encoding: utf-8 -*-
{
	'name': 'Reporte CUENTAS CORRIENTES',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para SALDOS POR FECHA CONTABLE, SALDOS POR FECHA DE DOC y DETALLE MOVIMIENTOS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_balance_doc_rep.xml',
		'views/account_balance_date.xml',
		'views/account_balance_period.xml',
		'views/account_balance_detail.xml'
	],
	'installable': True
}
