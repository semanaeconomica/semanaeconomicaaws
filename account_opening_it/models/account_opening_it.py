# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
import uuid
from datetime import datetime

class AccountOpeningIt(models.Model):
	_name = 'account.opening.it'

	@api.depends('from_fiscal_year_id','to_fiscal_year_id')
	def _get_name(self):
		for i in self:
			i.name = (i.from_fiscal_year_id.name if i.from_fiscal_year_id else '') + ' - ' + (i.to_fiscal_year_id.name if i.to_fiscal_year_id else '')

	name = fields.Char(compute=_get_name,store=True)
	from_fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio Anterior',required=True)
	to_fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio Actual',required=True)
	journal_id = fields.Many2one('account.journal',string='Diario Apertura',required=True)
	account_id = fields.Many2one('account.account',string='Cuenta de Resultado Acumulado',required=True)
	partner_id = fields.Many2one('res.partner',string='Partner Apertura',required=True)
	ref = fields.Char(string='Documento Apertura',required=True)
	state = fields.Selection([('draft','BORRADOR'),
							('done','REALIZADO')],string='Estado',default='draft')
	move_ids = fields.One2many('account.move','opening_id_it',string='Asientos de Apertura')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	def unlink(self):
		if self.state == 'done':
			raise UserError("No se puede eliminar una Apertura Contable si no esta en estado Borrador.")
		return super(AccountOpeningIt,self).unlink()

	def generate_opening(self):
		lines = []
		accounts = []
		#######PRIMER ASIENTO
		self.env.cr.execute("""SELECT account_id, activo, pasivo
			FROM get_f1_register('%s','%s',%d,'pen') WHERE activo+pasivo <> 0"""%(self.from_fiscal_year_id.name + '00',self.from_fiscal_year_id.name+'12',self.company_id.id))

		res = self.env.cr.dictfetchall()

		doc = self.env['einvoice.catalog.01'].search([('code','=','00')],limit=1)
		sum_debit = sum_credit = 0

		for elem in res:
			account_id = self.env['account.account'].browse(elem['account_id'])
			if account_id.is_document_an:
				accounts.append(elem)
			vals = (0,0,{
				'account_id': account_id.id,
				'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'debit': elem['activo'],
				'credit': elem['pasivo'],
				'currency_id': account_id.currency_id.id if account_id.currency_id else None,
				'amount_currency': self.get_amount_currency_account(account_id) if account_id.currency_id else 0,
				'partner_id': self.partner_id.id if account_id.is_document_an else None,
				'type_document_id': doc.id if account_id.is_document_an else None,
				'nro_comp': self.ref if account_id.is_document_an else None,
				'company_id': self.company_id.id,
				'amount_residual':0,
				'amount_residual_currency':0,
				'reconciled': True,
				'tc': abs(elem['activo'] - elem['pasivo'])/abs(self.get_amount_currency_account(account_id)) if account_id.currency_id else 1,
			})
			sum_debit += elem['activo']
			sum_credit += elem['pasivo']
			lines.append(vals)
		
		if sum_debit > sum_credit:
			vals = (0,0,{
				'account_id': self.account_id.id,
				'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'debit': 0,
				'credit': sum_debit-sum_credit,
				'company_id': self.company_id.id,
				'amount_residual':0,
				'amount_residual_currency':0,
				'reconciled': True,
			})
			lines.append(vals)
		
		if sum_debit < sum_credit:
			vals = (0,0,{
				'account_id': self.account_id.id,
				'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'debit': sum_credit-sum_debit,
				'credit': 0,
				'company_id': self.company_id.id,
				'amount_residual':0,
				'amount_residual_currency':0,
				'reconciled': True,
			})
			lines.append(vals)
		
		move = self.env['account.move'].create({
				'company_id': self.company_id.id,
				'journal_id': self.journal_id.id,
				'date': self.to_fiscal_year_id.date_from,
				'line_ids':lines,
				'ref': 'APERTURA',
				'glosa': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'is_opening_close':True,
				'opening_id_it': self.id,
				'type':'entry'})
		
		move.action_post()

		for account in accounts:
			account_id = self.env['account.account'].browse(account['account_id'])

			self.env.cr.execute("""SELECT T.periodo, T.fecha_con, T.partner_id, ei.id as type_document_id, T.nro_comprobante, T.saldo_mn, T.saldo_me 
			FROM get_saldos('%s','%s',%d,1) T 
			LEFT JOIN account_move_line aml on aml.id = T.move_line_id
			LEFT JOIN einvoice_catalog_01 ei ON ei.id = aml.type_document_id
			WHERE T.account_id = %d AND (T.periodo BETWEEN '%s' AND '%s')"""%(self.from_fiscal_year_id.date_from.strftime('%Y/%m/%d'),
													self.from_fiscal_year_id.date_to.strftime('%Y/%m/%d'),
													self.company_id.id,
													account_id.id,
													self.from_fiscal_year_id.name + '00',
													self.from_fiscal_year_id.name + '12'))
			
			line_data = self.env.cr.dictfetchall()
			line_account = []
			for line in line_data:
				vals = (0,0,{
					'account_id': account_id.id,
					'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
					'debit': line['saldo_mn'] if line['saldo_mn'] > 0 else 0,
					'credit': 0 if line['saldo_mn'] > 0 else abs(line['saldo_mn']),
					'currency_id': account_id.currency_id.id if account_id.currency_id else None,
					'amount_currency': line['saldo_me'] if account_id.currency_id else 0,
					'partner_id': line['partner_id'],
					'type_document_id': line['type_document_id'],
					'nro_comp': line['nro_comprobante'],
					'company_id': self.company_id.id,
					'amount_residual':0,
					'amount_residual_currency':0,
					'reconciled': True,
					'date_maturity':  line['fecha_con'] if line['fecha_con'] else None,
					'tc': abs(line['saldo_mn'])/abs(line['saldo_me']) if account_id.currency_id else 1,
				})
				line_account.append(vals)
			
			vals = (0,0,{
					'account_id': account_id.id,
					'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
					'debit': account['pasivo'],
					'credit': account['activo'],
					'currency_id': account_id.currency_id.id if account_id.currency_id else None,
					'amount_currency': (self.get_amount_currency_account(account_id) *-1) if account_id.currency_id else 0,
					'partner_id': self.partner_id.id,
					'type_document_id': doc.id,
					'nro_comp': self.ref,
					'company_id': self.company_id.id,
					'amount_residual':0,
					'amount_residual_currency':0,
					'reconciled': True,
					'tc': abs(account['pasivo']-account['activo'])/abs(self.get_amount_currency_account(account_id)) if account_id.currency_id else 1,
				})
			line_account.append(vals)

			move_account = self.env['account.move'].create({
				'company_id': self.company_id.id,
				'journal_id': self.journal_id.id,
				'date': self.to_fiscal_year_id.date_from,
				'line_ids':line_account,
				'ref': 'APERTURA ' + account_id.code,
				'glosa': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'is_opening_close':True,
				'opening_id_it': self.id,
				'type':'entry'})
		
			move_account.action_post()

		self.state = 'done'

	def get_amount_currency_account(self,account_id):
		self.env.cr.execute("""SELECT sum(coalesce(aml.amount_currency,0)) as amount_currency from account_move_line aml
		left join account_move am on am.id = aml.move_id
		where aml.account_id = %d and am.state = 'posted' and aml.company_id = %d
		AND (CASE
				WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
				WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
				ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer BETWEEN '%s' AND '%s')"""%(account_id.id,self.company_id.id,self.from_fiscal_year_id.name + '00',self.from_fiscal_year_id.name+'12'))

		res = self.env.cr.dictfetchall()
		if len(res) > 0:
			amount_currency = res[0]['amount_currency'] if res[0]['amount_currency'] else 0
			return amount_currency
		else:
			return 0

	def cancel_opening(self):
		for move in self.move_ids:
			if move.state =='draft':
				pass
			else:
				#for mm in move.line_ids:
				#	mm.remove_move_reconcile()
				move.button_cancel()
			move.line_ids.unlink()
			move.name = "/"
			move.unlink()

		self.state = 'draft'
	
	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', self.move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)