# -*- encoding: utf-8 -*-
{
	'name': 'Hr Advances and Loans',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it', 'hr_social_benefits'],
	'version': '1.0',
	'description':"""
	Modulo de Adelantos y Prestamos
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			 'security/ir.model.access.csv',
			 'views/hr_advance.xml',
			 'views/hr_gratification.xml',
			 'views/hr_loan.xml',
			 'views/hr_main_parameter.xml',
			 'views/hr_payslip.xml',
			 'views/hr_payslip_run.xml'],
	'installable': True
}
