# -*- encoding: utf-8 -*-
{
	'name': 'Tipo de Cambio de Cierre',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_base_it','l10n_pe_currency_rate'],
	'version': '1.0',
	'description':"""
	Sub-menu con Tabla de Tipos de Cambio de Cierre
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'wizards/account_exchange_rep.xml',
		'wizards/account_exchange_document_rep.xml',
		'views/exchange_diff_config.xml',
		'views/account_exchange_book.xml',
		'views/account_exchange_document_book.xml'
		],
	'installable': True
}
