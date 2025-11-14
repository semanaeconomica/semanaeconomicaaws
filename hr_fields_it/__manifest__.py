# -*- encoding: utf-8 -*-
{
	'name': 'Hr Fields IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_base_it','resource','report_tools'],
	'version': '1.0',
	'description':"""
	Modulo para agregar campos necesarios para la Localizacion Peruana de RRHH
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			 'security/security.xml',
			 'security/ir.model.access.csv',
			 'data/hr_payslip_input_type.xml',
			 'data/hr_salary_rule_category.xml',
			 'data/hr_salary_rule.xml',
			 'data/hr_payroll_structure.xml',
			 'wizard/hr_payroll_structure_wizard.xml',
			 'views/hr_employee.xml',
			 'views/hr_contract.xml',
			 'views/hr_salary_rule.xml',
			 'views/hr_salary_rule_category.xml',
			 'views/hr_payslip.xml',
			 'views/hr_payslip_run.xml',
			 'views/hr_payroll_structure.xml',
			 'views/hr_payslip_input_type.xml',
			 'report/hr_contract.xml',
			 'report/hr_employee.xml'],
	'installable': True
}
