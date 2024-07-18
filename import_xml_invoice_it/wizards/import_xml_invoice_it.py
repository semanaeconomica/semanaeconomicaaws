# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import base64
from lxml import etree

class ImportXmlInvoiceIt(models.TransientModel):
	_name = 'import.xml.invoice.it'

	lineas = fields.Many2many('ir.attachment', string='Archivos', required=True)
	type = fields.Selection([('in_invoice','Factura Proveedor'),('out_invoice','Factura Cliente'),('in_refund','Rectificativa Proveedor'),('out_refund','Rectificativa Cliente')],string='Tipo',default='in_invoice',required=True)
	journal_id = fields.Many2one('account.journal',string='Diario')
	expense_account_id = fields.Many2one('account.account',string='Cuenta de Gastos')
	income_account_id = fields.Many2one('account.account',string='Cuenta de Ingresos')

	def import_file(self):
		def _get_attachment_content(attachment):
			return hasattr(attachment, 'content') and getattr(attachment, 'content') or base64.b64decode(attachment.datas)

		import os
		import zipfile

		import_id = self.env['delete.move.xml.import'].create({
						'date': fields.Date.context_today(self),
						'company_id':self.env.company.id
					})

		for elem in self.lineas:               
			content = _get_attachment_content(elem)
			
			recibo = content.find(b'recibo.xsl')
			filename = elem.name
			def get_value(target_tree, xpath, namespaces):
				try:
					return target_tree.xpath(xpath, namespaces=namespaces)[0].text
				except IndexError as e:
					print(e)
					return ""
					
			if not filename.upper().endswith('.XML'):
				raise ValidationError('Wrong file format.')

			invoice = self.env['account.move'].create({
				'type' : self.type,
				'journal_id' : self.journal_id.id,
				'glosa': 'Importacion Facturas',
				'xml_import_code': import_id.id,
				'company_id' : self.env.company.id})

			type_invoice = invoice.type

			Issue_Date = False
			Sender_ID = False
			Currency_ID = False
			OrderReference = False
			Invoice_ID = False
			Tax_Amount_Total = False
			DueDate = False

			is_supplier = False
			is_customer = False
			supplier_rank = 0
			customer_rank = 0

			for line in invoice.invoice_line_ids:
				line.unlink()
			try:
				tree = etree.fromstring(content)

				ns = {"cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
						"cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
						"i2": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"}
				cabecera = True
				if self.type in ('in_invoice','out_invoice'):
					for x in tree.xpath("//cac:InvoiceLine", namespaces=ns):
						if cabecera:
							Issue_Date = get_value(x, "../cbc:IssueDate", ns)
							DueDate = get_value(x, "../cbc:DueDate", ns)
							Invoice_ID = get_value(x, "../cbc:ID", ns)
							OrderReference = get_value(x, "../cac:OrderReference/cbc:ID", ns)
							TypeDocument = get_value(x, "../cbc:InvoiceTypeCode", ns)
							Currency_Name = get_value(x, "../cbc:DocumentCurrencyCode", ns)
							Sender_ID = get_value(x, "../cac:AccountingCustomerParty/cbc:CustomerAssignedAccountID", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
							Receiver_ID = get_value(x, "../cac:AccountingSupplierParty/cbc:SupplierAssignedAccountID", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
							Tax_Amount_Total = get_value(x, "../cac:TaxTotal/cbc:TaxAmount", ns)
							Partner_Name = get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
							Supplier_Name = get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
							if type_invoice == 'in_invoice':
								Sender_ID = Receiver_ID
								Partner_Name = Supplier_Name
								supplier_rank = 1
								is_supplier = True
							else:
								customer_rank = 1
								is_customer = True
							cabecera = False
						Currency_ID = self.env['res.currency'].search([('name', 'ilike', Currency_Name)], limit=1)
						TypeDocumentID = self.env['einvoice.catalog.01'].search([('code', '=', TypeDocument)], limit=1)

						Product_Name = get_value(x, "cac:Item/cbc:Description", ns)
						Line_Quantity = get_value(x, "cbc:InvoicedQuantity", ns)
						Price_Unit = get_value(x, "cac:Price/cbc:PriceAmount", ns)
						tax_ids = []
						for t in tree.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=ns):
							Tax_Name = get_value(t, "cac:TaxCategory/cac:TaxScheme/cbc:ID", ns)
							tax_type = 'sale'
							if type_invoice == 'in_invoice':
								tax_type = 'purchase'
							Tax_Line_ID = self.env['account.tax'].search([('code_fe', '=', Tax_Name),('type_tax_use','=',tax_type),('company_id','=',self.env.company.id)], limit=1)
							if Tax_Line_ID.id:
								tax_ids.append(Tax_Line_ID.id)

						tem = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
						if len(tem) == 0:
							is_company = True
							if len(Sender_ID)==8:
								is_company = False
							else:
								if Sender_ID[:2] != '20':
									is_company = False
							vals = {
								'name': Partner_Name,
								'vat': Sender_ID,
								'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name','=','DNI')],limit=1).id if len(Sender_ID)==8 else self.env['l10n_latam.identification.type'].search(['|',('name','=','VAT'),('name','=','RUC')],limit=1).id,
								'is_company':is_company,
								'supplier_rank':supplier_rank,
								'is_supplier':is_supplier,
								'customer_rank':customer_rank,
								'is_customer':is_customer,
							}
							self.env['res.partner'].create(vals)
						invoice.partner_id = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
						invoice.currency_id = Currency_ID.id
						invoice.date = Issue_Date
						invoice.invoice_date = Issue_Date
						invoice.invoice_date_due = DueDate
						cuentaL = False
						if self.type in ('out_invoice'):
							cuentaL = self.income_account_id.id
						else:
							cuentaL = self.expense_account_id.id
						vals = {
							'name': Product_Name,
							'quantity': float(Line_Quantity),
							'price_unit': float(Price_Unit),
							'tax_ids': [(6, 0, tax_ids)],
							'account_id': cuentaL,
							'discount':0,
							'xml_import_code': import_id.id,
							'company_id':self.env.company.id,
							'currency_id':Currency_ID.id if Currency_ID.name != self.env.company.currency_id.name else None,
						}
						invoice.write({'invoice_line_ids' :([(0,0,vals)]) })
						for i in invoice.invoice_line_ids:
							i._onchange_price_subtotal()
				else:
					for x in tree.xpath("//cac:CreditNoteLine", namespaces=ns):
						if cabecera:
							Issue_Date = get_value(x, "../cbc:IssueDate", ns)
							DueDate = get_value(x, "../cbc:DueDate", ns)
							Invoice_ID = get_value(x, "../cbc:ID", ns)
							OrderReference = get_value(x, "../cac:InvoiceDocumentReference/cbc:ID", ns)
							TypeDocument = get_value(x, "../cbc:InvoiceTypeCode", ns)
							Currency_Name = get_value(x, "../cbc:DocumentCurrencyCode", ns)
							Sender_ID = get_value(x, "../cac:AccountingCustomerParty/cbc:CustomerAssignedAccountID", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
							Receiver_ID = get_value(x, "../cac:AccountingSupplierParty/cbc:SupplierAssignedAccountID", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
							Tax_Amount_Total = get_value(x, "../cac:TaxTotal/cbc:TaxAmount", ns)
							Partner_Name = get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
							Supplier_Name = get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
							if type_invoice == 'in_refund':
								Sender_ID = Receiver_ID
								Partner_Name = Supplier_Name
								supplier_rank = 1
								is_supplier = True
							else:
								customer_rank = 1
								is_customer = True
							cabecera = False
						Currency_ID = self.env['res.currency'].search([('name', 'ilike', Currency_Name)], limit=1)
						TypeDocumentID = self.env['einvoice.catalog.01'].search([('code', '=', TypeDocument)], limit=1)

						Product_Name = get_value(x, "cac:Item/cbc:Description", ns)
						Line_Quantity = get_value(x, "cbc:CreditedQuantity", ns)
						Price_Unit = get_value(x, "cac:Price/cbc:PriceAmount", ns)
						tax_ids = []
						for t in tree.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=ns):
							Tax_Name = get_value(t, "cac:TaxCategory/cac:TaxScheme/cbc:ID", ns)
							tax_type = 'sale'
							if type_invoice == 'in_refund':
								tax_type = 'purchase'
							Tax_Line_ID = self.env['account.tax'].search([('code_fe', '=', Tax_Name),('type_tax_use','=',tax_type),('company_id','=',self.env.company.id)], limit=1)
							if Tax_Line_ID.id:
								tax_ids.append(Tax_Line_ID.id)
					
						tem = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
						if len(tem) == 0:
							is_company = True
							if len(Sender_ID)==8:
								is_company = False
							else:
								if Sender_ID[:2] != '20':
									is_company = False
							vals = {
								'name': Partner_Name,
								'vat': Sender_ID,
								'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name','=','DNI')],limit=1).id if len(Sender_ID)==8 else self.env['l10n_latam.identification.type'].search(['|',('name','=','VAT'),('name','=','RUC')],limit=1).id,
								'is_company':is_company,
								'supplier_rank':supplier_rank,
								'is_supplier':is_supplier,
								'customer_rank':customer_rank,
								'is_customer':is_customer,
							}
							self.env['res.partner'].create(vals)
						invoice.partner_id = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
						invoice.currency_id = Currency_ID.id
						invoice.date = Issue_Date
						invoice.invoice_date = Issue_Date
						invoice.invoice_date_due = DueDate
						cuentaL = False
						if self.type in ('out_refund'):
							cuentaL = self.income_account_id.id
						else:
							cuentaL = self.expense_account_id.id

						vals = {
							'name': Product_Name,
							'quantity': float(Line_Quantity),
							'price_unit': float(Price_Unit),
							'tax_ids': [(6, 0, tax_ids)],
							'account_id': cuentaL,
							'discount':0,
							'xml_import_code': import_id.id,
							'company_id':self.env.company.id,
							'currency_id':Currency_ID.id if Currency_ID.name != self.env.company.currency_id.name else None,
						}
						invoice.write({'invoice_line_ids' :([(0,0,vals)]) })
						for i in invoice.invoice_line_ids:
							i._onchange_currency()

						fac_rel = self.env['account.move'].search([('ref','=',OrderReference),('partner_id','=',invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)[0].id),('company_id','=',self.env.company.id) ])
						if len(fac_rel)== 0:
							raise UserError('No existe el comprobante relacionado a la nota de Credito')
						else:
							fac_rel= fac_rel[0]
						self.env['doc.invoice.relac'].create({
							'type_document_id':fac_rel.type_document_id.id,
							'date':fac_rel.invoice_date,
							'nro_comprobante':OrderReference,
							'amount_currency':fac_rel.amount_total,
							'amount':fac_rel.amount_total* fac_rel.currency_rate,
							'bas_amount':fac_rel.amount_untaxed* fac_rel.currency_rate,
							'tax_amount':fac_rel.amount_total* fac_rel.currency_rate - fac_rel.amount_untaxed* fac_rel.currency_rate,
							'move_id':invoice.id,
							})
				
			except Exception as e:
				print(e)
				import sys, traceback
				exc_type, exc_value, exc_traceback = sys.exc_info()
				t= traceback.format_exception(exc_type, exc_value,exc_traceback)
				print(t)
				raise UserError(_(e))
				
			invoice.type_document_id = TypeDocumentID.id
			invoice.ref = Invoice_ID
			invoice.currency_id = Currency_ID.id
			type = invoice.type or self.env.context.get('type', 'out_invoice')

			if type in ('in_invoice', 'in_refund'):
				payment_term_id = invoice.partner_id.property_supplier_payment_term_id.id
			else:
				payment_term_id = invoice.partner_id.property_payment_term_id.id


			if len( self.env['account.move'].search([('ref','=',Invoice_ID),('company_id','=',self.env.company.id)]) ) > 1:
				invoice.unlink()
			else:

				invoice.ref = Invoice_ID
				invoice._get_ref()
				invoice.partner_shipping_id = invoice.partner_id
				invoice.payment_term_id = payment_term_id
				invoice.amount_tax = Tax_Amount_Total
				invoice.amount_total = invoice.amount_untaxed + invoice.amount_tax
				invoice._get_currency_rate()
				invoice._compute_amount()
				for line in invoice.line_ids.with_context(check_move_validity=False):
					line.partner_id = invoice.partner_id.id
					line.nro_comp = invoice.ref
					line.xml_import_code = import_id.id
					line.type_document_id = TypeDocumentID.id
					line.currency_id = invoice.currency_id.id if invoice.currency_id.name != self.env.company.currency_id.name else None
				

		return self.env['popup.it'].get_message(u'SE IMPORTARON CON EXITO LAS FACTURAS')