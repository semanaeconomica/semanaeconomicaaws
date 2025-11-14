# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountDetractionsWizard(models.TransientModel):
	_name = 'account.detractions.wizard'

	fecha = fields.Date(string='Fecha')
	monto = fields.Float(string='Monto',digits=(12,2))

	def generar(self):
		invoice = self.env['account.move'].browse(self.env.context['invoice_id'])
		m = self.env['main.parameter'].search([('company_id','=',invoice.company_id.id)],limit=1)

		if not m.detraction_journal.id:
			raise UserError(u"No esta configurada el Diario de Detracción en Parametros Principales de Contabilidad para su Compañía")

		flag_ver = True
		data = {
			'journal_id': m.detraction_journal.id,
			'ref':(invoice.ref if invoice.ref else 'Borrador'),
			'date': self.fecha,
			'invoice_date': invoice.invoice_date,
			'company_id': invoice.company_id.id,
			'glosa': 'PROVISION DE LA DETRACCION DE LA FACTURA ' + invoice.ref,
			'currency_rate': invoice.currency_rate,
			'type_op_det': invoice.type_op_det,
			'code_operation': invoice.code_operation,
		}
		if invoice.name_move_detraccion and invoice.diario_move_detraccion.id == m.detraction_journal.id and invoice.fecha_move_detraccion == invoice.invoice_date:
			data['name']= invoice.name_move_detraccion
			flag_ver = False
		else:
			invoice.diario_move_detraccion= m.detraction_journal.id
			invoice.fecha_move_detraccion = invoice.invoice_date
			flag_ver = True
		lines = []
		doc = self.env['einvoice.catalog.01'].search([('code','=','00')],limit=1)
		filtered_line = invoice.line_ids.filtered(lambda l: l.account_id.internal_type in ['receivable','payable'])
		if invoice.type == 'in_invoice':
			if not m.detractions_account.id:
				raise UserError(u"No esta configurada la Cuenta de Detracción para Proveedor en Parametros Principales de Contabilidad para su Compañía")
			if invoice.currency_id.name == 'USD':
				line_cc = (0,0,{
					'account_id': filtered_line.account_id.id,
					'debit': self.monto * invoice.currency_rate,
					'credit':0,
					'name':'DETRACCION - '+invoice.ref,
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'currency_id': invoice.currency_id.id,
					'amount_currency': self.monto,
					'tc': invoice.currency_rate,
					'company_id': invoice.company_id.id,			
					})
				lines.append(line_cc)

				line_cc = (0,0,{
					'account_id': m.detractions_account.id ,
					'debit': 0,
					'credit':self.monto * invoice.currency_rate,
					'name':'DETRACCION - '+invoice.ref,
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': doc.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

			else:
				line_cc = (0,0,{
					'account_id': filtered_line.account_id.id,
					'debit': self.monto,
					'credit':0,
					'name':'DETRACCION - '+invoice.ref,
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

				line_cc = (0,0,{
					'account_id': m.detractions_account.id ,
					'debit': 0,
					'credit':self.monto,
					'name':'DETRACCION - '+invoice.ref,
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': doc.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

		if invoice.type == 'out_invoice':
			if not m.customer_account_detractions.id:
				raise UserError(u"No esta configurada la Cuenta de Detracción para Clientes en Parametros Principales de Contabilidad para su Compañía")
			if invoice.currency_id.name == 'USD':
				line_cc = (0,0,{
					'account_id': m.customer_account_detractions.id ,
					'debit': self.monto * invoice.currency_rate,
					'credit':0,
					'name':'DETRACCION - '+invoice.ref,
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': doc.id,
					'company_id': invoice.company_id.id,			
					})
				lines.append(line_cc)

				line_cc = (0,0,{
					'account_id': filtered_line.account_id.id,
					'debit': 0,
					'credit':self.monto * invoice.currency_rate,
					'name':'DETRACCION - '+invoice.ref,
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'currency_id': invoice.currency_id.id,
					'amount_currency': abs(self.monto)*-1,
					'tc': invoice.currency_rate,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

			else:
				line_cc = (0,0,{
					'account_id': m.customer_account_detractions.id ,
					'debit': self.monto,
					'credit':0,
					'name':'DETRACCION - '+invoice.ref,
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': doc.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

				line_cc = (0,0,{
					'account_id': filtered_line.account_id.id,
					'debit': 0,
					'credit':self.monto,
					'name':'DETRACCION - '+invoice.ref,
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

		data['line_ids'] = lines
		tt = self.env['account.move'].create(data)
		ids_conciliation = []
		ids_conciliation.append(filtered_line.id)

		for line in tt.line_ids:
			if line.account_id == filtered_line.account_id and line.nro_comp == filtered_line.nro_comp and line.type_document_id == filtered_line.type_document_id and line.partner_id.id == filtered_line.partner_id.id:
				ids_conciliation.append(line.id)

		if len(ids_conciliation)>1:
			self.env['account.move.line'].browse(ids_conciliation).reconcile()

		if tt.state =='draft':
			tt.post()
		invoice.move_detraccion_id = tt.id

		if flag_ver:
			invoice.name_move_detraccion = tt.name

		return True