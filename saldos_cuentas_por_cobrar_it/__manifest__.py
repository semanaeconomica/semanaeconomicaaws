# -*- encoding: utf-8 -*-
{
	'name': 'Reporte de Saldos Cuentas por Cobrar',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_letras_it','sale','report_tools'],
	'version': '1.0',
	'description':"""
	Submenu para Reporte de Saldos Cuentas por Cobrar en Ventas
	Agrega campo en account.invoice -> DOCUMENTO ORIGEN CLIENTE
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'sql_functions.sql',
		'wizard/account_letras_saldos_rep.xml'
		],
	'installable': True
}
