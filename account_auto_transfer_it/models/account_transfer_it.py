# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError

class AccountTransferIt(models.Model):
	_name = 'account.transfer.it'

	name = fields.Char(string=u'Nro. Transferencia')
	glosa = fields.Char(string='Glosa')
	ref = fields.Char(string='Referencia')
	date_move = fields.Date(string='Fecha de Asiento',required=True)
	period = fields.Many2one('account.period',string='Periodo', required=True)
	journal_id = fields.Many2one('account.journal', required=True, string="Diario")
	state = fields.Selection([('draft','Borrador'),('done','En Proceso')],string='Estado',default='draft')
	account_ids = fields.One2many('account.transfer.account.line','transfer_id','Cuentas')
	distribution_ids = fields.One2many('account.transfer.distribution.line','transfer_id','Distribucion')
	move_id = fields.Many2one('account.move',string='Asiento Contable',readonly=True)
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Transferencias Automaticas')], limit=1)
		
		if not id_seq:
			id_seq = self.env['ir.sequence'].create({'name':'Transferencias Automaticas','implementation':'no_gap','active':True,'prefix':'TRANSF-','padding':5,'number_increment':1,'number_next_actual' :1})

		vals['name'] = id_seq._next()
		t = super(AccountTransferIt,self).create(vals)
		return t

	@api.constrains('distribution_ids')
	def _check_percent(self):
		total_percent = 0
		for i in self.distribution_ids:
			total_percent += i.percent
		
		if total_percent != 100:
			raise UserError('La suma de todas las lineas de distribucion tiene que ser 100%!')

	def state_check(self):
		for i in self.account_ids:
			if not i.analytic_account_id:
				self.env.cr.execute(self._get_sql_account(i.account_id.id,self.period.date_start,self.period.date_end,0))
			else:
				self.env.cr.execute(self._get_sql_account(i.account_id.id,self.period.date_start,self.period.date_end,1,i.analytic_account_id.id))
			obj =self.env.cr.fetchall()
			for elemnt in obj:
				i.debit = elemnt[1]
				i.credit = elemnt[2]
				if elemnt[3] < 0:
					raise UserError("La cuenta "+i.account_id.name+" tiene balance negativo.")
				i.balance = elemnt[3]

	def preview(self):
		self.env.cr.execute("""
			CREATE OR REPLACE view account_transfer_book as (SELECT row_number() OVER () AS id, t.* from ("""+self._get_sql_preview(self.id)+""")t)""")

		return {
			'name': 'Vista Preliminar',
			'type': 'ir.actions.act_window',
			'res_model': 'account.transfer.book',
			'view_mode': 'tree',
			'view_type': 'form',
			'target': 'new',
		}

	def crear_asiento(self):
		lineas = []
		
		self.env.cr.execute(self._get_sql_preview(self.id))
		obj =self.env.cr.fetchall()
		sum_credit = 0
		sum_debit = 0
		for elemnt in obj:
			vals = (0,0,{
					'account_id': elemnt[4],
					'nro_comp':self.ref,
					'name':self.glosa,
					'debit': elemnt[1],
					'credit': elemnt[2],
					'analytic_account_id':elemnt[5],
					'company_id': self.company_id.id
			})
			lineas.append(vals)
			sum_debit += float(elemnt[1])
			sum_credit += float(elemnt[2])

		if sum_debit - sum_credit < 0:
			rounding_loss_account = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).rounding_loss_account
			if not rounding_loss_account:
				raise UserError(u'No existe Cuenta de Pérdida en Parametros Principales de Contabilidad para su Compañía')
			vals = (0,0,{
					'account_id': rounding_loss_account.id,
					'nro_comp':self.ref,
					'name':self.glosa,
					'debit': abs(sum_debit - sum_credit),
					'credit': 0,
					'company_id': self.company_id.id
			})
			lineas.append(vals)

		if sum_debit - sum_credit > 0:
			rounding_gain_account = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).rounding_gain_account
			if not rounding_gain_account:
				raise UserError(u'No existe Cuenta de Ganancia en Parametros Principales de Contabilidad para su Compañía')
			vals = (0,0,{
					'account_id': rounding_gain_account.id,
					'nro_comp':self.ref,
					'name':self.glosa,
					'debit': 0,
					'credit': abs(sum_debit - sum_credit),
					'company_id': self.company_id.id
			})
			lineas.append(vals)

		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': self.journal_id.id,
			'date': self.date_move,
			'line_ids':lineas,
			'ref': self.ref,
			'glosa':self.glosa,
			'type':'entry'})

		move_id.post()
		self.move_id = move_id.id
		self.state = 'done'

	def cancelar(self):
		if self.move_id.id:
			if self.move_id.state =='draft':
				pass
			else:
				self.move_id.button_cancel()
			self.move_id.line_ids.unlink()
			self.move_id.name = "/"
			self.move_id.unlink()

		self.state = 'draft'

	def  _get_sql_preview(self,id):
		sql = """
				select
				b2.cuenta,
				round(cast(b1.porcentaje*b2.credit as numeric),2) as debit,
				0 as credit,
				b1.cta_analitica,
				b2.account_id,
				b1.analytic_account_id
				from 
				(select
					1 as jjoin,
					0 as debe,
					0 as haber,
					ana.name as cta_analitica,
					atdl.percent/100 as porcentaje,
					ana.id as analytic_account_id
					from account_transfer_distribution_line atdl
					left join account_analytic_account ana on ana.id = atdl.analytic_account_id
					where atdl.transfer_id = %s)b1
				left join (select
				aa.code as cuenta,
				1 as jjoin,
				atal.balance as credit,
				aa.id as account_id
				from account_transfer_account_line atal
				left join account_account aa on aa.id = atal.account_id
				where atal.transfer_id = %s)b2 on b1.jjoin = b2.jjoin
				union all
				select aa.code as cuenta,
				0 as debit,
				atal.balance as credit,
				ana.name as cta_analitica,
				aa.id as account_id,
				ana.id as analytic_account_id
				from account_transfer_account_line atal
				left join account_account aa on aa.id = atal.account_id
				left join account_analytic_account ana on ana.id = atal.analytic_account_id
				where atal.transfer_id = %s
			""" % (str(id),str(id),str(id))

		return sql

	def _get_sql_account(self,account_id,date_start,date_end,analytic,analytic_account_id=None):
		sql_analytic = ""
		if analytic == 1:
			sql_analytic = "and aml.analytic_account_id = %s" % (str(analytic_account_id))
		sql = """
				select 
					aa.id as cuenta,
					sum(aml.debit) as debit,
					sum(aml.credit) as credit,
					sum(aml.balance) as balance
					from account_move_line aml
					left join account_account aa on aa.id = aml.account_id
					left join account_move am on am.id = aml.move_id
					where aa.id = %s and (am.date between '%s' and '%s') %s
					group by aa.id
			""" % (str(account_id),
				date_start.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				sql_analytic)

		return sql


class AccountTransferAccountLine(models.Model):
	_name = 'account.transfer.account.line'

	transfer_id = fields.Many2one('account.transfer.it','Transferencia')
	account_id = fields.Many2one('account.account',string='Cuenta',required=True)
	analytic_account_id = fields.Many2one('account.analytic.account',string='Cta. Analitica')
	debit = fields.Float(string='Debe', digits=(64,2),readonly=True)
	credit = fields.Float(string='Haber', digits=(64,2),readonly=True)
	balance = fields.Float(string='Balance', digits=(64,2),readonly=True)

class AccountTransferDistributionLine(models.Model):
	_name = 'account.transfer.distribution.line'

	transfer_id = fields.Many2one('account.transfer.it','Transferencia')
	analytic_account_id = fields.Many2one('account.analytic.account',string='Cta. Analitica')
	percent = fields.Float(string="Porcentaje (%)", required=True, default=100)