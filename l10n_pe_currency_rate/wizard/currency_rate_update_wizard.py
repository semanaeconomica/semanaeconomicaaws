# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning, UserError

class PeCurrencyRateUpdateWizard(models.TransientModel):
	
	_name = "pe.currency.rate.update.wizard"
	_description = 'PE Currency Rate Update Wizard'
	
	rate_update_id = fields.Many2one("pe.currency.rate.update.service", "Rate update", 
									 default = lambda self: self.env.context.get('active_ids',[]) and self.env.context.get('active_ids',[])[0] or False)
	start_date = fields.Date("Start date")
	end_date = fields.Date("End date")

	document_file = fields.Binary(string='Excel')
	name_file = fields.Char(string='Nombre de Archivo')

	def importar(self):
		if not self.document_file:
			raise UserError('Tiene que cargar un archivo.')
		
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)
		except:
			raise Warning(_("Archivo invalido!"))

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 4:
					date_string = False
					if line[0] != '':
						a1 = int(float(line[0]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					values = ({'date':date_string,
								'sale_type':line[1],
								'purchase_type': line[2],
								'rate': line[3],
								})
					self.make_currency_rate(values)
				elif len(line) > 4:
					raise Warning(_('Tu archivo tiene columnas mas columnas de lo esperado.'))
				else:
					raise Warning(_('Tu archivo tiene columnas menos columnas de lo esperado.'))

		return self.env['popup.it'].get_message(u'SE IMPORTO CON EXITO LOS TIPOS DE CAMBIO.')

	def make_currency_rate(self, values):
		rate_obj = self.env['res.currency.rate']
		currency = self.env.ref('base.USD')
		if currency:
			if not values.get('date'):
				raise Warning(_('El campo "name" no puede estar vacio.'))

			rate_search = rate_obj.search([
						('name', '=', values.get('date')),
						('currency_id', '=', currency.id),
						('company_id','=',self.env.company.id)
					],limit=1)

			if rate_search:
				rate_search.write({
					'rate': values.get('rate'),
					'sale_type': values.get('sale_type'),
					'purchase_type': values.get('purchase_type'),
				})
			else:
				rate_obj.create({
					'currency_id': currency.id,
					'rate': values.get('rate'),
					'name': values.get('date'),
					'sale_type': values.get('sale_type'),
					'purchase_type': values.get('purchase_type'),
					'company_id': self.env.company.id
				})
	
	#@api.one
	#def get_currency_rate(self):
	#    start_date = fields.Date.from_string(self.start_date)
	#    end_date = fields.Date.from_string(self.end_date)
	#    days = end_date - start_date
	#    if days.days < 0:
	#        raise ValidationError(_('The end date must be greater than the start date'))
	#    
	#    while days.days >= 0:
	#        day = days.days
	#        self.with_context(date = fields.Date.to_string(end_date)).rate_update_id.refresh_currency()
	#        day -=1
	#        end_date = start_date + timedelta(day)
	#        days = end_date - start_date

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_currency_rate',
			 'target': 'new',
			 }