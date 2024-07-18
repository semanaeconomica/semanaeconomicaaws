from odoo import models, fields, api, _
from odoo.tools.misc import formatLang, format_date, get_lang
from datetime import datetime
import pytz

DATE_FORMAT = '%d/%m/%Y'
TZ = pytz.timezone('America/Lima')

class AccountFollowupReport(models.AbstractModel):
	_inherit = "account.followup.report"

	def _get_columns_name(self, options):
		headers = super(AccountFollowupReport, self)._get_columns_name(options)
		if self.env.context.get('print_mode'):
			headers[4].update({
				'name':'Documento'
				})
			headers[3].update({
				'name':''
				})
		return headers

	def _get_lines(self, options, line_id=None):
		lines = super(AccountFollowupReport, self)._get_lines(options, line_id)
		if self.env.context.get('print_mode'):
			for l in lines:
				l.update({'name':''})
				l['columns'][2].update({'name':''})
				print('=========')
				print(l)
				print('=========')
		return lines