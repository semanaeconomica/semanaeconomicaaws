# -*- encoding: utf-8 -*-
{
	'name': 'Period Generator',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','account_base_it','account_journal_sequence'],
	'version': '1.0',
	'description':"""
	Generador de Periodos Automatico en base a un Año Fiscal
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/wizard_period_generator.xml'],
	'installable': True
}
