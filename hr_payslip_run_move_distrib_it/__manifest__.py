# -*- encoding: utf-8 -*-
{
	'name': 'Hr Payslip Run Move distribuido IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_payslip_run_move_it'],
	'version': '1.0',
	'description':"""
	Modulo para generar Asiento Contable de Nomina por Lotes distribuido
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'hr_functions.sql',
			],
	'installable': True
}