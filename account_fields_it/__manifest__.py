# -*- encoding: utf-8 -*-
{
	'name': 'Account Fields IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','analytic','base','account_base_it','account_batch_payment','product'],
	'version': '1.0',
	'description':"""
	Modificacion del modelo account.account
	Modificacion del modelo account.analytic
	Modificacion del modelo res.partner
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/account_account.xml',
			'views/account_payment.xml',
			'views/account_move.xml',
			'views/analytic_account.xml',
			'views/res_partner.xml',
			'views/account_bank_statement.xml',
			'views/account_batch_payment.xml',
			'views/product_category.xml',
			'views/account_group.xml',
			'views/account_move_line.xml',
			'views/account_journal.xml',
			'views/account_chart_template.xml',
			'views/account_account_tag.xml'
			],
	'installable': True
}
