# -*- encoding: utf-8 -*-
{
	'name': 'Hr Payslip Run Move IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it', 'report_tools', 'popup_it'],
	'version': '1.0',
	'description':"""
	Modulo para generar Asiento Contable de Nomina por Lotes
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/hr_payslip_run.xml',
			'views/hr_payslip_run_move.xml',
			'wizard/hr_payslip_run_move_wizard.xml',
			'hr_functions.sql'],
	'installable': True
}