# -*- encoding: utf-8 -*-
{
	'name': 'Guias de Remision',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['base','account','stock','kardex_fisico_it','fleet','popup_it','account_base_it','sales_team','purchase'],
	'version': '1.0',
	'description':"""
	Guias de Remision 
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/einvoice_catalog_20.xml',
		'views/fleet_vehicle.xml',
		'views/res_partner.xml',
		'views/main_parameter_warehouse.xml',
		'views/stock_picking_type.xml',
		'views/stock_picking.xml',
		'views/einvoice_catalog_20.xml',
		'wizards/confirm_date_picking.xml',
		'wizards/stock_picking_wizard.xml'
	],
	'installable': True
}