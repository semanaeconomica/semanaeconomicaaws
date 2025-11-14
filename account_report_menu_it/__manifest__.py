# -*- encoding: utf-8 -*-
{
	'name': 'Menu Reportes de Localizacion Contable',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account', 'account_base_it', 'tax_register_voucher', 'report_tools'],
	'version': '1.0',
	'description':"""
        MENU DE REPORTES PARA LOCALIZACION CONTABLE
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
	'libro_contables_peruanos.sql',
	'estados_financieros_peruanos.sql',
	'cuentas_corrientes.sql',
        'views/account_report_menu_it.xml'
    ],
	'installable': True
}
