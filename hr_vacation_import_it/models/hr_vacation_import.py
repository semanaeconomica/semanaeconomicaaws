from openerp import models, fields, exceptions, api, _
import tempfile
import binascii
import xlrd
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from openerp.exceptions import Warning, UserError
import io
import logging
_logger = logging.getLogger(__name__)

try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')
try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')


class HrRestImport(models.TransientModel):
	_name = "hr.rest.import"

	file = fields.Binary(string='Archivo')
	year = fields.Char(u'Año')
	

	def hr_vacation_import(self):			  
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		try :
			fp.write(binascii.a2b_base64(self.file))
			fp.seek(0)
			values = {}
			res = {}
			workbook = xlrd.open_workbook(fp.name)
		except Exception:
				raise exceptions.Warning(_("Sube un archivo .xlsx!")) 
		sheet = workbook.sheet_by_index(0)
		caderror=''
		for row_no in range(sheet.nrows):
			val = {}
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				date_time_str=self.year+'-01-01 00:00:00'
				date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')				
				
				
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if str(line[1])[-2:]=='.0':
					cad = str(line[1])[:-2]
				else:
					cad=str(line[1])

				if str(line[2])[-2:]=='.0':
					caddays = str(line[2])[:-2]
				else:
					caddays=str(line[2])

				empl_exist = self.env['hr.employee'].search([('identification_id','=',cad)])
				
				if not empl_exist:
					caderror=caderror+'No existe el documento:' +cad+'\n'
					continue
				vals={
					'employee_id':empl_exist.id,
					'date_from':date_time_obj.date(),
					'date_end':date_time_obj.date(),
					'internal_motive':'rest',
					'motive':'Saldo acumulado anterior',
					'days':0,
					'days_rest':int(caddays),
					'year':self.year
				}
				self.env['hr.vacation.rest'].create(vals)
				
		return self.env['popup.it'].get_message('SE IMPORTARON LOS SALDOS. con cexcepción de:\n'+caderror)
	

	

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_hr_rest_import_template',
			 'target': 'new',
			}