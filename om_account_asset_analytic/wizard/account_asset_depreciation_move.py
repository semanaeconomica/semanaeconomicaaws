# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountAssetDepreciationMove(models.TransientModel):
	_name = 'account.asset.depreciation.move'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company)
	period = fields.Many2one('account.period',string=u'Periodo',required=True)

	def asset_compute(self):
		self.ensure_one()
		self.env.cr.execute("""select account_analytic_id, account_analytic_tag_id, account_depreciation_expense_id as account_id, sum(valor_dep) as debit, 0 as credit, (select id from einvoice_catalog_01 where code = '00' limit 1) as type_document_id
			from get_activos('%s','%s',%d)
			group by account_analytic_id, account_analytic_tag_id, account_depreciation_expense_id
			union all 
			select null as account_analytic_id, null as account_analytic_tag_id, account_depreciation_id as account_id, 0 as debit, sum(valor_dep) as credit, (select id from einvoice_catalog_01 where code = '00' limit 1) as type_document_id
			from get_activos('%s','%s',%d)
			group by account_depreciation_id"""%(self.period.date_start.strftime('%Y/%m/%d'),
			self.period.date_end.strftime('%Y/%m/%d'),
			self.company_id.id,
			self.period.date_start.strftime('%Y/%m/%d'),
			self.period.date_end.strftime('%Y/%m/%d'),
			self.company_id.id))

		res = self.env.cr.dictfetchall()

		destination_journal = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).destination_journal

		if not destination_journal:
			raise UserError(u'No existe un Diario Asiento Automático configurado en Parametros Generales de Contabilidad para su Compañía.')

		lineas = []

		for elemnt in res:
			tag_ids = []
			if elemnt['account_analytic_tag_id']:
				tag_ids.append(elemnt['account_analytic_tag_id'])

			vals = (0,0,{
				'analytic_account_id': elemnt['account_analytic_id'],
				'analytic_tag_ids':([(6,0,tag_ids)]),
				'account_id': elemnt['account_id'],
				'name': u'DEPRECIACIÓN '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.period.fiscal_year_id.name,
				'debit': elemnt['debit'],
				'credit': elemnt['credit'],
				'type_document_id': elemnt['type_document_id'],
				'nro_comp': 'dep-'+str('{:02d}'.format(self.period.date_start.month))+'-'+self.period.fiscal_year_id.name,
				'tc':1,
				'company_id': self.company_id.id,
			})
			lineas.append(vals)

		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': destination_journal.id,
			'date': self.period.date_end,
			'ref': 'dep-'+str('{:02d}'.format(self.period.date_start.month))+'-'+self.period.fiscal_year_id.name,
			'glosa': u'DEPRECIACIÓN DE ACTIVOS DE '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.period.fiscal_year_id.name,
			'line_ids':lineas})

		move_id.post()

		self.env.cr.execute("""select line_depreciation_id
			from get_activos('%s','%s',%d)"""%(self.period.date_start.strftime('%Y/%m/%d'),
			self.period.date_end.strftime('%Y/%m/%d'),
			self.company_id.id))

		res_ids = self.env.cr.dictfetchall()

		for line_id in res_ids:
			line = self.env['account.asset.depreciation.line'].browse(line_id["line_depreciation_id"])
			if line.move_id:
				line.move_id.button_cancel()
				line.move_id.line_ids.unlink()
				line.move_id.name = "/"
				line.move_id.unlink()
			line.write({'move_id': move_id.id, 'move_check': True})
			

		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': move_id.id,
		}