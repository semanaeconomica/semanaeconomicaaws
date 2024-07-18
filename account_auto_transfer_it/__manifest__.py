# -*- encoding: utf-8 -*-
{
	'name': 'Distribuciones Analiticas IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_base_it','account_auto_transfer','analytic'],
	'version': '1.0',
	'description':"""
	Modulo que para distribuciones analiticas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			 'security/security.xml',
			 'security/ir.model.access.csv',
			 'views/account_transfer_book.xml',
			 'views/account_transfer_it.xml'
			 ],
	'installable': True
}
