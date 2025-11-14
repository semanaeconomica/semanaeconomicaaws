# -*- encoding: utf-8 -*-
{
	'name': 'Import XML Invoice',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','import_journal_entry_it'],
	'version': '1.0',
	'description':"""
	Modulo para importar Facturas desde XML
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'security/security.xml',
		'security/ir.model.access.csv',
		'wizards/import_xml_invoice_it.xml',
		'wizards/change_account_account_wizard.xml',
        'views/delete_move_xml_import.xml',
        'views/account_move_line.xml',
		'views/account_tax.xml'
	],
	'installable': True
}