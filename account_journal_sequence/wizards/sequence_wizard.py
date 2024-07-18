# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class SequenceWizard(models.TransientModel):
	_name = 'sequence.wizard'

	name = fields.Char()
	fiscal_id = fields.Many2one('account.fiscal.year',u'Año Fiscal')
	journal_id = fields.Many2one('account.journal')

	def generar_secuencia(self):
		day = 1
		month = 1
		year = int(self.fiscal_id.name)
		self.journal_id.sequence_id.use_date_range = True
		self.journal_id.sequence_id.prefix = '%(range_month)s-'
		self.journal_id.sequence_id.padding = 6
		self.journal_id.sequence_id.code = 'account.journal'
		delete_data = self.env['ir.sequence.date_range'].search([('date_from','=',str(datetime(day=day,month=month,year=year))[:10]),('date_to','=',str(datetime(day=31,month=12,year=year))[:10]),('sequence_id','=',self.journal_id.sequence_id.id)])
		if delete_data:
			for date_r in delete_data:
				print(date_r)
				date_r.unlink()
		for fech in range(12):
			dia_1 = datetime(day=day,month=month,year=year)
			month+= 1
			if month == 13:
				month= 1
				year+= 1

			dia_2 = datetime(day=day,month=month,year=year) - timedelta(days=1)
			busqueda = self.env['ir.sequence.date_range'].search([('date_from','=',str(dia_1)[:10]),('date_to','=',str(dia_2)[:10]),('sequence_id','=',self.journal_id.sequence_id.id)])
			if len(busqueda)==0:
				data = {
					'date_from':str(dia_1)[:10],
					'date_to':str(dia_2)[:10],
					'sequence_id':self.journal_id.sequence_id.id,
					'number_next_actual':1,
				}
				self.env['ir.sequence.date_range'].create(data)

		return self.env['popup.it'].get_message("Se ha generado las secuencias para el ejercicio fiscal '"+self.fiscal_id.name+"'" + ", y el diario '"+self.journal_id.name+"'")