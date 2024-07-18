# -*- coding: utf-8 -*-

from odoo import models, fields, api
BILLING_TYPE = [('0','Nubefact'),('1','Odoo Facturacion')]

class MainParameter(models.Model):
	_inherit = 'main.parameter'
	advance_product_ids = fields.One2many('advance.product.line','main_parameter_id')
	resolution = fields.Char(string=u'Resolución')
	web_query = fields.Char(string='Web Consulta')
	external_download_url = fields.Char(string='URL Descarga Externa')
	serial_nubefact_lines = fields.One2many('serial.nubefact.line','main_parameter_id')
	billing_type = fields.Selection(BILLING_TYPE,string='Tipo de Facturador')
	igv_tax_id = fields.Many2one('account.tax',string='Impuesto IGV')
	doc_origin_customer_check = fields.Boolean(string='Utilizar Documento Origen Cliente', default=False)
	invoice_origin_check = fields.Boolean(string='Utilizar Documento Origen en Observaciones', default=False)
	catalog_51_detraction_ids = fields.Many2many('einvoice.catalog.51', 'catalog_51_detraction_parameter_rel', string='Tipos de Operacion Sujetos a Detraccion')
	catalog_51_advance_ids = fields.Many2many('einvoice.catalog.51', 'catalog_51_advance_parameter_rel', string='Tipos de Operacion Sujetos a Anticipos')
	comment_add_check = fields.Boolean(string='Agregar comentario de factura a envio CPE', default=True)
	bank_numbers = fields.Text(string='Cuentas de banco')

class SerialNubefactLine(models.Model):
	_name = 'serial.nubefact.line'
	_description = "holas"

	main_parameter_id = fields.Many2one('main.parameter')
	serie_id = fields.Many2one('it.invoice.serie',string='Serie')
	nubefact_token = fields.Char(string='Token')
	nubefact_path = fields.Char(string='URL')
	billing_type = fields.Selection(BILLING_TYPE,string='Tipo de Facturador')
	is_einvoice = fields.Boolean(string='Fact. Electronica')

class AdvanceProductLine(models.Model):
	_name = 'advance.product.line'
	_description = "holas"

	main_parameter_id = fields.Many2one('main.parameter')
	product_id = fields.Many2one('product.product',string='Producto Anticipo')