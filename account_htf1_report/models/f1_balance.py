# -*- coding: utf-8 -*-

from odoo import models, fields, api

class F1Balance(models.Model):
	_name = 'f1.balance'
	_auto = False
	_order = 'mayor'

	period_from = fields.Char(string='Periodo Inicio')
	period_to = fields.Char(string='Periodo Final')
	mayor = fields.Char(string='Mayor')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe')
	haber = fields.Float(string='Haber')
	saldo_deudor = fields.Float(string='Saldo Deudor')
	saldo_acreedor = fields.Float(string='Saldo Acreedor')
	activo = fields.Float(string='Activo')
	pasivo = fields.Float(string='Pasivo')
	perdinat = fields.Float(string='Perdinat')
	ganannat = fields.Float(string='Ganannat')
	perdifun = fields.Float(string='Perdifun')
	gananfun = fields.Float(string='Gananfun')

	def view_detail(self):
		self.env.cr.execute("""SELECT move_line_id FROM vst_diariog 
								WHERE (CAST(periodo AS int ) BETWEEN CAST('%s' AS int ) AND CAST('%s' AS int )) 
								AND left(cuenta,2) = '%s'
								AND company_id = %s""" % (self.period_from,self.period_to,self.mayor,str(self.env.company.id)))
		res = self.env.cr.dictfetchall()
		elem = []
		for key in res:
			elem.append(key['move_line_id'])

		return {
			'name': 'Detalle',
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.line',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': '_blank',
		}