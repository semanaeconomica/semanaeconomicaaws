# -*- encoding: utf-8 -*-
{
	'name': 'Hr Base IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['popup_it','hr_payroll','hr_payroll_account','hr'],
	'version': '1.0',
	'description':"""
	Modulo base para Nomina
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			 'security/ir.model.access.csv',
			 'data/hr_payroll_structure_type.xml',
			 'data/hr_payroll_structure.xml',
			 'data/hr_payslip_worked_days_type.xml',
			 'data/hr_membership.xml',
			 'data/hr_situation.xml',
			 'data/hr_social_insurance.xml',
			 'data/hr_suspension_type.xml',
			 'data/hr_type_document.xml',
			 'data/hr_workday.xml',
			 'data/hr_worker_type.xml',
			 'views/hr_main_parameter.xml',
			 'views/hr_analytic_distribution.xml',
			 'views/hr_holidays.xml',
			 'views/hr_membership.xml',
			 'wizard/hr_membership_wizard.xml',
			 'views/hr_payslip_worked_days_type.xml',
			 'views/hr_sctr.xml',
			 'views/hr_situation.xml',
			 'views/hr_social_insurance.xml',
			 'views/hr_suspension_type.xml',
			 'views/hr_type_document.xml',
			 'views/hr_workday.xml',
			 'views/hr_worker_type.xml',
			 'views/hr_menus.xml'],
	'installable': True
}
