# -*- coding: utf-8 -*-

from odoo import models, fields, api

class F2Register(models.Model):
	_name = 'f2.register'
	_auto = False
	_order = 'mayor'

	period = fields.Char(string='Periodo')
	mayor = fields.Char(string='Mayor')
	cuenta = fields.Char(string='Cuenta')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe_inicial = fields.Float(string='Debe Inicial')
	haber_inicial = fields.Float(string='Haber Inicial')
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
	rubro = fields.Char(string='Rubro Estado Financiero')

	def view_detail(self):
		self.env.cr.execute("""SELECT move_line_id FROM vst_diariog 
								WHERE CAST(periodo AS int ) = CAST('%s' AS int )
								AND cuenta = '%s'
								AND company_id = %s""" % (self.period,self.cuenta,str(self.env.company.id)))
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