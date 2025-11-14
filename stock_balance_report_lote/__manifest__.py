# -*- encoding: utf-8 -*-
{
	'name': 'Stock Balance Report',
	'category': 'stock',
	'author': 'ITGRUPO',
	'depends': ['stock_balance_report','kardex_fisico_it_multi_lote','kardex_lote_vencimiento'],
	'version': '1.0',
	'description':"""
	Reporte de Saldos
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/stock_balance_report.xml'
	],
	'installable': True
}
