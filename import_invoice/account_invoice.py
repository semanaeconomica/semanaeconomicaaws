# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import tempfile
import binascii
import xlrd
import io
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning , UserError
from odoo import models, fields, exceptions, api, _

import logging
_logger = logging.getLogger(__name__)

try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')


TYPE2JOURNAL = {
	'out_invoice': 'sale',
	'in_invoice': 'purchase',
	'out_refund': 'sale',
	'in_refund': 'purchase',
}

class AccountMove(models.Model):
	_inherit = "account.move"

	custom_seq = fields.Boolean('Custom Sequence')
	system_seq = fields.Boolean('System Sequence')
	invoice_name = fields.Char('Invoice Name')

class gen_inv(models.TransientModel):
	_name = "gen.invoice"

	file = fields.Binary('File')
	account_opt = fields.Selection([('default', 'Use Account From Configuration product/Property'), ('custom', 'Use Account From Excel/CSV')], string='Account Option', required=True, default='default')
	type = fields.Selection([('in', 'Customer'), ('out', 'Supplier'),('cus_credit_note','Customer Credit Note'),('ven_credit_note','Vendor Credit Note')], string='Type', required=True, default='in')
	sequence_opt = fields.Selection([('custom', 'Use Excel/CSV Sequence Number'), ('system', 'Use System Default Sequence Number')], string='Sequence Option',default='custom')
	import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='xls')
	sample_option = fields.Selection([('csv', 'CSV'),('xls', 'XLS')],string='Sample Type',default='xls')
	down_samp_file = fields.Boolean(string='Download Sample Files')
	stage = fields.Selection(
		[('draft', 'Import Draft Invoice'), ('confirm', 'Validate Invoice Automatically With Import')],
		string="Invoice Stage Option", default='draft')
	import_prod_option = fields.Selection([('name', 'Name'),('code', 'Code'),('barcode', 'Barcode')],string='Import Product By ',default='name')
	journal_id = fields.Many2one('account.journal',string='Diario',required=True)
	option_statement = fields.Selection([('render','Entregas a Rendir'),('cash','Caja Chica')],string='Statement',default='cash')
	render_id = fields.Many2one('account.bank.statement',string='N° Rendicion',domain=[('journal_type', '=', 'cash'),('journal_check_surrender', '=', True)])
	cash_id = fields.Many2one('account.bank.statement',string='N° Caja Chica',domain=[('journal_type', '=', 'cash'),('journal_check_surrender', '=', False)])
	
	def make_invoice(self, values):
		invoice_obj = self.env['account.move']
		if self.sequence_opt == "custom":
			if self.type == "in":
				invoice_search = invoice_obj.search([
					('name', '=', values.get('invoice')),
					('type', '=', 'out_invoice'),
					('custom_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			elif self.type == 'out':
				invoice_search = invoice_obj.search([
					('name', '=', values.get('invoice')),
					('type', '=', 'in_invoice'),
					('custom_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			elif self.type == 'cus_credit_note':
				invoice_search = invoice_obj.search([
					('name', '=', values.get('invoice')),
					('type', '=', 'out_refund'),
					('custom_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			else:
				invoice_search = invoice_obj.search([
					('name', '=', values.get('invoice')),
					('type', '=', 'in_refund'),
					('custom_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
		else:
			if self.type == "in":
				invoice_search = invoice_obj.search([
					('invoice_name', '=', values.get('invoice')),
					('type', '=', 'out_invoice'),
					('system_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			elif self.type == 'out':
				invoice_search = invoice_obj.search([
					('invoice_name', '=', values.get('invoice')),
					('type', '=', 'in_invoice'),
					('system_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			elif self.type == 'cus_credit_note':
				invoice_search = invoice_obj.search([
					('invoice_name', '=', values.get('invoice')),
					('type', '=', 'out_refund'),
					('system_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			else:
				invoice_search = invoice_obj.search([
					('invoice_name', '=', values.get('invoice')),
					('type', '=', 'in_refund'),
					('system_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			
		if invoice_search:
			if invoice_search.partner_id.vat != str(values.get('customer')):
				raise Warning(_('Customer name is different for "%s" .\n Please define same.') % values.get('customer'))

			if  invoice_search.currency_id.name != values.get('currency'):
				raise Warning(_('Currency is different for "%s" .\n Please define same.') % values.get('currency'))

			if  invoice_search.invoice_user_id.name != values.get('salesperson'):
				raise Warning(_('User(Salesperson) is different for "%s" .\n Please define same.') % values.get('salesperson'))

			if invoice_search.type_document_id.code != str(values.get('td')):
				raise Warning(_('Type Document is different for "%s" .\n Please define same.') % values.get('td'))

			if invoice_search.ref != str(values.get('nro_comprobante')):
				raise Warning(_('Invoice Number is different for "%s" .\n Please define same.') % values.get('nro_comprobante'))

			if invoice_search.glosa != values.get('glosa'):
				raise Warning(_('Glosa is different for "%s" .\n Please define same.') % values.get('glosa'))

			if invoice_search.state != 'draft':
				raise Warning(_('Invoice "%s" is not in Draft state.') % invoice_search.name)

			self.make_invoice_line(values, invoice_search)
			return invoice_search
						
		else:
			if str(values.get('customer')) == '':
				raise Warning(_('Please assign a Partner.'))
			else:
				partner_id = self.find_partner(str(values.get('customer')))
			currency_id = self.find_currency(values.get('currency'))
			salesperson_id = self.find_sales_person(values.get('salesperson'))
			if values.get('date_invoice') == '':
				raise Warning(_('Please assign a date'))
			else:
				inv_date = self.find_invoice_date(values.get('date_invoice'))

			if str(values.get('td')) == '':
				raise Warning(_('Please assign a Type Document.'))
			else:
				type_document_id = self.find_type_document(str(values.get('td')))

			if str(values.get('nro_comprobante')) == '':
				raise Warning(_('Please assign a Invoice Number.'))

			if str(values.get('glosa')) == '':
				raise Warning(_('Please assign a Glosa.'))

			if self.type == "in":
				type_inv = "out_invoice"
				if partner_id.property_account_receivable_id:
					account_id = partner_id.property_account_receivable_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_receivable_id')])
					account_id = account_search.value_reference
					if not account_id:
						raise UserError(_('Please define Customer account.'))
					account_id = account_id.split(",")[1]
					account_id = self.env['account.account'].browse(account_id)
					
			elif self.type == "out":
				type_inv = "in_invoice"
				if partner_id.property_account_payable_id:
					account_id = partner_id.property_account_payable_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_payable_id')])
					account_id = account_search.value_reference
					if not account_id:
						raise UserError(_('Please define Vendor account.'))
					account_id = account_id.split(",")[1]
					account_id = self.env['account.account'].browse(account_id)
			   
			elif self.type == "cus_credit_note":
				type_inv = "out_refund"
				if partner_id.property_account_receivable_id:
					account_id = partner_id.property_account_receivable_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_receivable_id')])
					account_id = account_search.value_reference
					if not account_id:
						raise UserError(_('Please define Customer account.'))
					account_id = account_id.split(",")[1]
					account_id = self.env['account.account'].browse(account_id)
			else:
				type_inv = "in_refund"
				if partner_id.property_account_payable_id:
					account_id = partner_id.property_account_payable_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_payable_id')])
					account_id = account_search.value_reference
					if not account_id:
						raise UserError(_('Please define Vendor account.'))
					account_id = account_id.split(",")[1]
					account_id = self.env['account.account'].browse(account_id)
			inv_id = invoice_obj.create({
				'name': values.get('invoice') if self.sequence_opt == 'custom' else '/',
				'partner_id' : partner_id.id,
				'currency_id' : currency_id.id,
				'invoice_user_id':salesperson_id.id,
				'custom_seq': True if self.sequence_opt == 'custom' else False,
				'system_seq': True if self.sequence_opt == 'system' else False,
				'type' : type_inv,
				'date':inv_date,
				'invoice_date':inv_date,
				'journal_id' : self.journal_id.id,
				'invoice_name' : values.get('invoice'),
				'type_document_id' : type_document_id.id,
				'ref' : str(values.get('nro_comprobante')),
				'glosa': str(values.get('glosa')),
				'company_id' : self.env.company.id
			})
			inv_id._get_currency_rate()
			self.make_invoice_line(values, inv_id)
			return inv_id
	
	def make_invoice_line(self, values, inv_id):
		product_obj = self.env['product.product']

		if self.import_prod_option == 'barcode':
		  product_search = product_obj.search([('barcode',  '=',values['product'])])
		elif self.import_prod_option == 'code':
			product_search = product_obj.search([('default_code', '=',values['product'])])
		else:
			product_search = product_obj.search([('name', '=',values['product'])])

		product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
		if not product_uom:
			raise Warning(_(' "%s" Product UOM category is not available.') % values.get('uom'))

		if product_search:
			product_id = product_search
		else:
			if self.import_prod_option == 'name':
				product_id = product_obj.create({
													'name':values.get('product'),
													'lst_price':values.get('price'),
													'uom_id':product_uom.id,
												 })
			else:
				raise Warning(_('%s product is not found" .\n If you want to create product then first select Import Product By Name option .') % values.get('product'))

		tax_ids = []
		if inv_id.type == 'out_invoice':
			if values.get('tax'):
				if ';' in  values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in  values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax').split(',')
					tax= self.env['account.tax'].search([('name', '=', tax_names),('type_tax_use','=','sale')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)
		elif inv_id.type == 'in_invoice':
			if values.get('tax'):
				if ';' in values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax').split(',')
					tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)
		elif inv_id.type == 'out_refund':
			if values.get('tax'):
				if ';' in  values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in  values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax').split(',')
					tax= self.env['account.tax'].search([('name', '=', tax_names),('type_tax_use','=','sale')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)
		else:
			if values.get('tax'):
				if ';' in values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax').split(',')
					tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)

		if self.account_opt == 'default':
			if inv_id.type == 'out_invoice':
				if product_id.property_account_income_id:
					account = product_id.property_account_income_id
				elif product_id.categ_id.property_account_income_categ_id:
					account = product_id.categ_id.property_account_income_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id')])
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)
			if inv_id.type == 'in_invoice':
				if product_id.property_account_expense_id:
					account = product_id.property_account_expense_id
				elif product_id.categ_id.property_account_expense_categ_id:
					account = product_id.categ_id.property_account_expense_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id')])
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)

			if inv_id.type == 'out_refund':
				if product_id.property_account_income_id:
					account = product_id.property_account_income_id
				elif product_id.categ_id.property_account_income_categ_id:
					account = product_id.categ_id.property_account_income_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id')])
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)
			if inv_id.type == 'in_refund':
				if product_id.property_account_expense_id:
					account = product_id.property_account_expense_id
				elif product_id.categ_id.property_account_expense_categ_id:
					account = product_id.categ_id.property_account_expense_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id')])
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)

		else:
			if values.get('account') == '':
				raise Warning(_(' You can not left blank account field if you select Excel/CSV Account Option'))
			else:
				if self.import_option == 'csv':
					account_id = self.env['account.account'].search([('code','=',values.get('account')),('company_id','=',self.env.company.id)])
				else:
					account_id = self.env['account.account'].search([('code','=',values.get('account')),('company_id','=',self.env.company.id)])
				if account_id:
					account = account_id
				else:
					raise Warning(_(' "%s" Account is not available.') % values.get('account')) 

		analytic_account_id = False

		if values.get("analytic_account_id"):
			analytic_account_id = self.find_analytic_account(values.get("analytic_account_id"))

		vals = {
			'product_id' : product_id.id,
			'quantity' : values.get('quantity'),
			'price_unit' :values.get('price'),
			'discount':values.get('discount'),
			'name' : values.get('description'),
			'account_id' : account.id,
			'analytic_account_id': analytic_account_id.id if analytic_account_id else None,
			'product_uom_id' : product_uom.id,
			'company_id' : self.env.company.id
		}
		if tax_ids:
			vals.update({'tax_ids':([(6,0,tax_ids)])})

		inv_id.write({'invoice_line_ids' :([(0,0,vals)]) })
		inv_id.write({'code_import_invoice': values.get("import_id")})    
		
		return inv_id

	def find_analytic_account(self, code):
		analytic_obj = self.env['account.analytic.account']
		analytic_search = analytic_obj.search([('code', '=', str(code)),('company_id','=',self.env.company.id)],limit=1)
		if analytic_search:
			return analytic_search
		else:
			raise Warning(_('No existe una Cuenta Analitica con el Codigo "%s" en esta Compañia') % code)

	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)],limit=1)
		if currency_search:
			return currency_search
		else:
			raise Warning(_(' "%s" Currency are not available.') % name)

	
	def find_sales_person(self, name):
		sals_person_obj = self.env['res.users']
		partner_search = sals_person_obj.search([('name', '=', name)],limit=1)
		if partner_search:
			return partner_search
		else:
			raise Warning(_('Not Valid Salesperson Name "%s"') % name)


	
	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise Warning(_('No existe un Partner con el Nro de Documento "%s"') % name)

	def find_type_document(self,name):
		type_document_search = self.env['einvoice.catalog.01'].search([('code','=',str(name))],limit=1)
		if type_document_search:
			return type_document_search
		else:
			raise Warning(_('No existe un Tipo de Comprobante con el Codigo"%s"') % name)
	
	def find_invoice_date(self, date):
		DATETIME_FORMAT = "%Y-%m-%d"
		i_date = datetime.strptime(date, DATETIME_FORMAT).date()
		return i_date

	
	def import_csv(self):
		"""Load Inventory data from the CSV file."""
		if self.import_option == 'csv':
			if self.account_opt == 'default':
				keys = ['invoice', 'customer', 'currency', 'product', 'quantity', 'uom', 'description', 'price','discount','salesperson','tax','date','analytic_account_id']
			else:
				keys = ['invoice', 'customer', 'currency', 'product','account', 'quantity', 'uom', 'description', 'price','discount','salesperson','tax','date','analytic_account_id']
			
			try:
				csv_data = base64.b64decode(self.file)
				data_file = io.StringIO(csv_data.decode("utf-8"))
				data_file.seek(0)
				file_reader = []
				csv_reader = csv.reader(data_file, delimiter=',')
				file_reader.extend(csv_reader)
			except Exception:
				raise exceptions.Warning(_("Please select an CSV/XLS file or You have selected invalid file"))
			values = {}
			invoice_ids=[]
			for i in range(len(file_reader)):
				field = list(map(str, file_reader[i]))
				if self.account_opt == 'default':
					if len(field) > 12:
						raise Warning(_('Your File has extra column please refer sample file'))
					elif len(field) < 12:
						raise Warning(_('Your File has less column please refer sample file'))
				else:
					if len(field) > 13:
						raise Warning(_('Your File has extra column please refer sample file'))
					elif len(field) < 13:
						raise Warning(_('Your File has less column please refer sample file'))

				values = dict(zip(keys, field))
				if values:
					if i == 0:
						continue
					else:
						values.update({'type':self.type,'option':self.import_option,'seq_opt':self.sequence_opt})
						res = self.make_invoice(values)
						invoice_ids.append(res)

			if self.stage == 'confirm':
				for res in invoice_ids: 
					if res.state in ['draft']:
						res.action_post()

		else:
			try:
				fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
				fp.write(binascii.a2b_base64(self.file))
				fp.seek(0)
				values = {}
				invoice_ids=[]
				workbook = xlrd.open_workbook(fp.name)
				sheet = workbook.sheet_by_index(0)
			except Exception:
				raise exceptions.Warning(_("Please select an CSV/XLS file or You have selected invalid file"))

			import_id = self.env['delete.account.move.import'].create({
						'date': fields.Date.context_today(self),
						'company_id':self.env.company.id,
						'nro_entrega': self.render_id.sequence_number if self.render_id else '',
						'nro_caja': self.cash_id.sequence_number if self.cash_id else '',
					})

			for row_no in range(sheet.nrows):
				val = {}
				if row_no <= 0:
					continue
				else:
					line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
					if self.account_opt == 'default':
						if len(line) == 17:
							if line[11] == '':
								raise Warning(_('Please assign a date'))
							else:
								a1 = int(float(line[11]))
								a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
								date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
							if line[12] == '':
								raise Warning(_('Please assign a invoice date'))
							else:
								a1_i = int(float(line[12]))
								a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
								date_invoice_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
							values.update( {'invoice':line[0],
											'customer': str(line[1]),
											'currency': line[2],
											'product': line[3].split('.')[0],
											'quantity': line[4],
											'uom': line[5],
											'description': line[6],
											'price': line[7],
											'discount':line[8],
											'salesperson': line[9],
											'tax': line[10],
											'date': date_string,
											'date_invoice': date_invoice_string,
											'seq_opt':self.sequence_opt,
											'td': str(line[13]),
											'nro_comprobante': str(line[14]),
											'glosa': str(line[15]),
											'analytic_account_id': str(line[16]),
											#'tc_per': str(line[17]),
											'import_id':import_id.id
											})
						elif len(line) > 17:
							raise Warning(_('Your File has extra column please refer sample file'))
						else:
							raise Warning(_('Your File has less column please refer sample file'))
					else:
						if len(line) == 18:
							if line[12] == '':
								raise Warning(_('Please assign a date'))
							else:
								a1 = int(float(line[12]))
								a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
								date_string = a1_as_datetime.date().strftime('%Y-%m-%d')

							if line[13] == '':
								raise Warning(_('Please assign a invoice date'))
							else:
								a1_i = int(float(line[13]))
								a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
								date_invoice_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
							values.update( {'invoice':line[0],
											'customer': str(line[1]),
											'currency': line[2],
											'product': line[3].split('.')[0],
											'account': line[4],
											'quantity': line[5],
											'uom': line[6],
											'description': line[7],
											'price': line[8],
											'discount':line[9],
											'salesperson': line[10],
											'tax': line[11],
											'date': date_string,
											'date_invoice': date_invoice_string,
											'seq_opt':self.sequence_opt,
											'td': str(line[14]),
											'nro_comprobante': str(line[15]),
											'glosa': str(line[16]),
											'analytic_account_id': str(line[17]),
											#'tc_per': str(line[18]),
											'import_id':import_id.id
											})
						elif len(line) > 18:
							raise Warning(_('Your File has extra column please refer sample file'))
						else:
							raise Warning(_('Your File has less column please refer sample file'))
					res = self.make_invoice(values)
					res._get_currency_rate()
					print(res.currency_rate)
					res._compute_amount()
					res.flush()
					if date_string != date_invoice_string:
						print(date_string)
						print(date_invoice_string)
						res.write({'date': date_string})
						#if str(line[18]) == 'SI':
						#	res.write({'tc_per': True})
						#	print(res.id)
						#	res._onchange_currency()
						#	res._onchange_recompute_dynamic_lines()
					invoice_ids.append(res)

			if self.stage == 'confirm':
				for res in invoice_ids: 
					if res.state in ['draft']:
						res.action_post()

			return res


	def download_auto(self):
		
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_document?model=gen.invoice&id=%s'%(self.id),
			 'target': 'new',
			 }

