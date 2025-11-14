# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import datetime

class AccountLetrasPayment(models.Model):
	_name = 'account.letras.payment'

	name = fields.Char(string=u'Nro. Canje')
	partner_id = fields.Many2one('res.partner',string='Partner')
	date_exchange = fields.Date(string='Fecha Canje')
	glosa = fields.Char(string='Glosa')
	reference = fields.Char(string='Referencia')
	journal_id = fields.Many2one('account.journal',string='Diario')
	factura_ids = fields.One2many('account.letras.payment.factura','letra_payment_id','Facturas')
	letras_manual_ids = fields.One2many('account.letras.payment.manual','letra_payment_id','Letras Manual')
	residual_ids = fields.One2many('account.letras.payment.residual','letra_payment_id','Redondeo')
	asiento_id = fields.Many2one('account.move',string='Asiento Contable')
	state = fields.Selection([('draft','Borrador'),('check','Comprobado'),('done','Finalizado')],string='Estado',default='draft')
	type = fields.Selection([('out','Cliente'),('in','Proveedor')],string='Tipo')
	tipo_cambio = fields.Float(string='Tipo de Cambio',digits=(12,4),default=1)
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	def unlink(self):
		for letra in self:
			if letra.state in ('check','done'):
				raise UserError("No puede eliminar un Canje de Letra que ya fue Comprobado.")
		return super(AccountLetrasPayment, self).unlink()

	@api.onchange('date_exchange')
	def on_change_date_exchange(self):
		if self.date_exchange:
			divisa_line = self.env['res.currency.rate'].search([('name','=',self.date_exchange)])
			if len(divisa_line)>0:
				self.tipo_cambio = divisa_line[0].sale_type

			for i in self.letras_manual_ids:
				i.date_exchange = self.date_exchange
				i._update_debit_credit()

	@api.onchange('tipo_cambio')
	def on_change_tc(self):
		if self.tipo_cambio:
			for i in self.letras_manual_ids:
				i.tipo_cambio = self.tipo_cambio
				i._update_debit_credit()

	@api.onchange('partner_id')
	def on_change_partner_id(self):
		if self.partner_id:
			for i in self.letras_manual_ids:
				i.partner_id = self.partner_id

	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Canje de Letra Customer')], limit=1)
		if self.env.context.get('default_type') == 'out':
			id_seq = self.env['ir.sequence'].search([('name','=','Canje de Letra Customer')], limit=1)
			if not id_seq:
				if not id_seq:
					id_seq = self.env['ir.sequence'].create({'name':'Canje de Letra Customer','implementation':'no_gap','active':True,'prefix':'CLC-','padding':5,'number_increment':1,'number_next_actual' :1})
		
		if self.env.context.get('default_type') == 'in':
			id_seq = self.env['ir.sequence'].search([('name','=','Canje de Letra Supplier')], limit=1)
			if not id_seq:
				if not id_seq:
					id_seq = self.env['ir.sequence'].create({'name':'Canje de Letra Supplier','implementation':'no_gap','active':True,'prefix':'CLP-','padding':5,'number_increment':1,'number_next_actual' :1})

		vals['name'] = id_seq._next()
		t = super(AccountLetrasPayment,self).create(vals)
		return t

	def state_check(self):
		tot_debit = 0
		tot_credit = 0

		for i in self.factura_ids:
			tot_debit += i.debit
			tot_credit += i.credit
			i.get_account()

		for i in self.letras_manual_ids:
			tot_debit += i.debit
			tot_credit += i.credit
			i.get_account()

		param = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if not param:
			raise UserError(u'No existen Parametros Principales de Contabilidad para su Compañía')

		account_id_param = False
		debit_param = 0
		credit_param = 0

		if tot_debit-tot_credit < 0:
			debit_param = abs(tot_debit-tot_credit)
			account_id_param = param.rounding_loss_account.id
		if tot_debit-tot_credit > 0:
			credit_param = tot_debit-tot_credit
			account_id_param = param.rounding_gain_account.id

		self.env['account.letras.payment.residual'].create({
				'letra_payment_id': self.id,
				'account_id': account_id_param,
				'debit': debit_param,
				'credit': credit_param,
				'comprobante': self.reference,
			})

		self.state = 'check'

	def change_draft(self):
		for i in self.residual_ids:
			i.unlink()
		self.state = 'draft'

	def cancelar(self):
		if self.asiento_id.id:
			if self.asiento_id.state =='draft':
				pass
			else:
				for mm in self.asiento_id.line_ids:
					mm.remove_move_reconcile()
				self.asiento_id.button_cancel()
			self.asiento_id.line_ids.unlink()
			self.asiento_id.name = "/"
			self.asiento_id.unlink()

		for i in self.residual_ids:
			i.unlink()
		self.state = 'draft'

	def crear_asiento(self):
		lineas = []

		for elemnt in self.factura_ids:
			if elemnt.currency_id.name != 'PEN':
				amm_res = elemnt.imp_div*self.tipo_cambio
				vals = (0,0,{
					'account_id': elemnt.account_id.id,
					'partner_id':self.partner_id.id,
					'type_document_id':elemnt.type_document_id.id,
					'nro_comp': elemnt.nro_comprobante,
					'name': 'CANJE DE LETRAS POR FACTURA',
					'currency_id': elemnt.currency_id.id,
					'amount_currency': elemnt.imp_div,
					'debit': elemnt.debit,
					'credit': elemnt.credit,
					'date_maturity':False,
					'company_id': self.company_id.id,
					'amount_residual': amm_res,
					'amount_residual_currency': elemnt.imp_div,
					'tc': self.tipo_cambio,
					'reconciled':False,
				})
				lineas.append(vals)
			else:
				vals = (0,0,{
					'account_id': elemnt.account_id.id,
					'partner_id':self.partner_id.id,
					'type_document_id':elemnt.type_document_id.id,
					'nro_comp': elemnt.nro_comprobante,
					'name': 'CANJE DE LETRAS POR FACTURA',
					'debit': elemnt.debit,
					'credit': elemnt.credit,
					'date_maturity':False,
					'company_id': self.company_id.id,
					'amount_residual': elemnt.imp_div,
					'reconciled':False,
				})
				lineas.append(vals)
		
		for elemnt in self.letras_manual_ids:
			if elemnt.currency_id.name != 'PEN':
				amm_res = elemnt.imp_div*self.tipo_cambio
				vals = (0,0,{
					'account_id': elemnt.account_id.id,
					'partner_id':self.partner_id.id,
					'type_document_id':self.env['einvoice.catalog.01'].search([('code','=','00')])[0].id,
					'nro_comp': elemnt.nro_letra,
					'name': 'CANJE DE LETRAS POR FACTURA',
					'currency_id': elemnt.currency_id.id,
					'amount_currency': elemnt.imp_div,
					'debit': elemnt.debit,
					'credit': elemnt.credit,
					'date_maturity':elemnt.expiration_date,
					'company_id': self.company_id.id,
					'amount_residual': amm_res,
					'amount_residual_currency': elemnt.imp_div,
					'tc': self.tipo_cambio,
					'reconciled':False,
				})
				lineas.append(vals)
			else:
				vals = (0,0,{
					'account_id': elemnt.account_id.id,
					'partner_id':self.partner_id.id,
					'type_document_id':self.env['einvoice.catalog.01'].search([('code','=','00')])[0].id,
					'nro_comp': elemnt.nro_letra,
					'name': 'CANJE DE LETRAS POR FACTURA',
					'debit': elemnt.debit,
					'credit': elemnt.credit,
					'date_maturity':elemnt.expiration_date,
					'company_id': self.company_id.id,
					'amount_residual': elemnt.imp_div,
					'reconciled':False,
				})
				lineas.append(vals)

		for elemnt in self.residual_ids:
			if elemnt.debit == 0 and elemnt.credit == 0:
				pass
			else:
				vals = (0,0,{
					'account_id': elemnt.account_id.id,
					'partner_id':self.partner_id.id,
					'name': 'REDONDEO',
					'debit': elemnt.debit,
					'credit': elemnt.credit,
					'date_maturity':False,
					'company_id': self.company_id.id,
				})
				lineas.append(vals)
			
		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': self.journal_id.id,
			'date': self.date_exchange,
			'line_ids':lineas,
			'ref': self.name,
			'glosa':self.glosa,
			'type':'entry'})

		for c,elemnt in enumerate(self.factura_ids):
			ids_conciliation = []
			ids_conciliation.append(move_id.line_ids[c].id)

			for line in elemnt.move_id.line_ids:
				if line.account_id.id == move_id.line_ids[c].account_id.id and line.nro_comp == move_id.line_ids[c].nro_comp and line.type_document_id == move_id.line_ids[c].type_document_id and line.partner_id.id == move_id.line_ids[c].partner_id.id:
					ids_conciliation.append(line.id)

			if len(ids_conciliation)>1:
				self.env['account.move.line'].browse(ids_conciliation).reconcile()

		move_id.post()
		self.asiento_id = move_id.id
		self.state = 'done'

class AccountLetrasPaymentFactura(models.Model):
	_name = 'account.letras.payment.factura'

	letra_payment_id = fields.Many2one('account.letras.payment','Pago')
	type_document_id = fields.Many2one('einvoice.catalog.01',string='Tipo de Documento')
	move_id = fields.Many2one('account.move',string='Factura')
	nro_comprobante = fields.Char(string='Nro de Comprobante',related='move_id.ref')
	account_id = fields.Many2one('account.account',string='Cuenta',compute='get_account')
	currency_id = fields.Many2one('res.currency',string='Moneda',related='move_id.currency_id')
	saldo = fields.Monetary(string='Saldo',digits=(12,2),related='move_id.amount_residual')
	imp_div = fields.Float(string='Importe Div',digits=(12,2))
	debit = fields.Float(string='Debe',digits=(64,2),default=0,compute='_update_debit_credit')
	credit = fields.Float(string='Haber',digits=(64,2),default=0,compute='_update_debit_credit')

	@api.onchange('imp_div')
	def _update_debit_credit(self):
		for i in self:
			if i.imp_div:
				if i.currency_id.name != 'PEN':
					i.debit = i.imp_div * i.letra_payment_id.tipo_cambio if i.imp_div > 0 else 0
					i.credit = 0 if i.imp_div > 0 else abs(i.imp_div * i.letra_payment_id.tipo_cambio)
				else:
					i.debit = i.imp_div if i.imp_div > 0 else 0
					i.credit = 0 if i.imp_div > 0 else abs(i.imp_div)

	@api.onchange('currency_id')
	def get_account(self):
		param = self.env['main.parameter'].search([('company_id','=',self.letra_payment_id.company_id.id)],limit=1)
		for let in self:
			if not param:
				raise UserError(u'No existen Parametros Principales de Contabilidad para su Compañía')

			if let.letra_payment_id.type == 'out':
				let.account_id = param.customer_invoice_account_fc.id if let.currency_id.name != 'PEN' else param.customer_invoice_account_nc.id
			if let.letra_payment_id.type == 'in':
				let.account_id =  param.supplier_invoice_account_fc.id if let.currency_id.name != 'PEN' else param.supplier_invoice_account_nc.id
			
class AccountLetrasPaymentManual(models.Model):
	_name = 'account.letras.payment.manual'

	@api.depends('nro_letra')
	def _get_name(self):
		for i in self:
			i.name = i.nro_letra

	name = fields.Char(compute=_get_name,store=True)
	letra_payment_id = fields.Many2one('account.letras.payment','Pago',copy=False)
	letra_user_id = fields.Many2one('res.users',string='Vendedor',default=lambda self: self.env.user)
	nro_letra = fields.Char(string=u'Nro. de Letra',default='Letra')
	currency_id = fields.Many2one('res.currency',string='Moneda')
	account_id = fields.Many2one('account.account',string='Cuenta')
	expiration_date = fields.Date(string='Fecha Vencimiento')
	imp_div = fields.Float(string='Importe Div',digits=(12,2),default=0)
	debit = fields.Float(string='Debe',digits=(64,2),default=0)
	credit = fields.Float(string='Haber',digits=(64,2),default=0)
	tipo_cambio = fields.Float(string='Tipo de Cambio',digits=(12,4),default=1)
	partner_id = fields.Many2one('res.partner',string='Partner')
	date_exchange = fields.Date(string='Fecha Emision')
	type = fields.Selection([('out','Cliente'),('in','Proveedor')],string='Tipo')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	@api.onchange('date_exchange')
	def get_tc(self):
		if self.date_exchange:
			divisa_line = self.env['res.currency.rate'].search([('name','=',self.date_exchange)])
			if len(divisa_line)>0:
				self.tipo_cambio = divisa_line[0].sale_type 

	@api.onchange('currency_id')
	def get_account(self):
		self.ensure_one()
		param = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if not param:
			raise UserError(u'No existen Parametros Principales de Contabilidad para su Compañía')

		if self.letra_payment_id.type == 'out' or self.env.context.get('default_type') == 'out':
			self.account_id = param.customer_letter_account_fc.id if self.currency_id.name != 'PEN' else param.customer_letter_account_nc.id
		if self.letra_payment_id.type == 'in' or self.env.context.get('default_type') == 'in':
			self.account_id =  param.supplier_letter_account_fc.id if self.currency_id.name != 'PEN' else param.supplier_letter_account_nc.id

		if self.letra_payment_id:
			self.tipo_cambio = self.letra_payment_id.tipo_cambio
			self.partner_id = self.letra_payment_id.partner_id
			self.date_exchange = self.letra_payment_id.date_exchange

	@api.onchange('imp_div','currency_id','tipo_cambio','date_exchange')
	def _update_debit_credit(self):
		if self.imp_div and self.currency_id:
			if self.currency_id and self.currency_id.name != 'PEN':
				self.debit = self.imp_div * self.tipo_cambio if self.imp_div > 0 else 0
				self.credit = 0 if self.imp_div > 0 else abs(self.imp_div * self.tipo_cambio)
			else:
				self.debit = self.imp_div if self.imp_div > 0 else 0
				self.credit = 0 if self.imp_div > 0 else abs(self.imp_div)

	def write(self, vals):
		for letra in self:
			if letra.letra_payment_id and letra.letra_payment_id.state in ('check','done'):
				raise UserError("No puede editar una Letra que se encuentra en un canje.")
		return super(AccountLetrasPaymentManual, self).write(vals)

	def unlink(self):
		for letra in self:
			if letra.letra_payment_id and letra.letra_payment_id.state in ('check','done'):
				raise UserError("No puede eliminar una Letra que se encuentra en un canje.")
		return super(AccountLetrasPaymentManual, self).unlink()

class AccountLetrasPaymentResidual(models.Model):
	_name = 'account.letras.payment.residual'

	letra_payment_id = fields.Many2one('account.letras.payment','Pago')
	comprobante = fields.Char(string='Comprobante')
	account_id = fields.Many2one('account.account',string='Cuenta')
	debit = fields.Float(string='Debe',digits=(64,2))
	credit = fields.Float(string='Haber',digits=(64,2))
		
	