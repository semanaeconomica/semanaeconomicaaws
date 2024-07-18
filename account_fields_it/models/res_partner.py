# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
from psycopg2 import sql, DatabaseError
from odoo.exceptions import ValidationError,UserError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
	_inherit = 'res.partner'

	is_not_home = fields.Boolean(string='No Domiciliado', default=False)
	country_home_nd = fields.Char(help='Tabla 35 SUNAT', string='Pais Residencia del N.D.',size=4)
	home_nd = fields.Char(string='Domicilio en el Extranjero del N.D.',size=200)
	ide_nd = fields.Char(string='Numero de Identificacion del sujeto N.D.',size=50)
	v_con_nd = fields.Char(help='Tabla 27 SUNAT', string='Vinculo entre el Contribuyente y el Residente Extranjero',size=2)
	c_d_imp = fields.Char(help='Tabla 25 SUNAT', string='Convenio para Evitar Doble Imposicion',size=2)
	name_p = fields.Char(string='Nombre',size=200)
	last_name = fields.Char(string='Apellido Paterno',size=200)
	m_last_name = fields.Char(string='Apellido Materno',size=200)
	p_detraction = fields.Float(string='Porcentaje Detraccion',digits=(12,2))
	is_customer = fields.Boolean(string='Cliente',default=False)
	is_employee = fields.Boolean(string='Empleado',default=False)
	is_supplier = fields.Boolean(string='Proveedor', default=False)

	def _decrease_rank_it(self, field):
		if self.ids and field in ['customer_rank', 'supplier_rank']:
			try:
				with self.env.cr.savepoint():
					query = sql.SQL("""
						SELECT {field} FROM res_partner WHERE ID IN %(partner_ids)s FOR UPDATE NOWAIT;
						UPDATE res_partner SET {field} = {field} - 1
						WHERE id IN %(partner_ids)s
					""").format(field=sql.Identifier(field))
					self.env.cr.execute(query, {'partner_ids': tuple(self.ids)})
					for partner in self:
						self.env.cache.remove(partner, partner._fields[field])
			except DatabaseError as e:
				if e.pgcode == '55P03':
					_logger.debug('Another transaction already locked partner rows. Cannot update partner ranks.')
				else:
					raise e

	def _increase_rank_it(self, field):
		if self.ids and field in ['customer_rank', 'supplier_rank']:
			try:
				with self.env.cr.savepoint():
					query = sql.SQL("""
						SELECT {field} FROM res_partner WHERE ID IN %(partner_ids)s FOR UPDATE NOWAIT;
						UPDATE res_partner SET {field} = {field} + 1
						WHERE id IN %(partner_ids)s
					""").format(field=sql.Identifier(field))
					self.env.cr.execute(query, {'partner_ids': tuple(self.ids)})
					for partner in self:
						self.env.cache.remove(partner, partner._fields[field])
			except DatabaseError as e:
				if e.pgcode == '55P03':
					_logger.debug('Another transaction already locked partner rows. Cannot update partner ranks.')
				else:
					raise e
	
	@api.constrains('vat','l10n_latam_identification_type_id','parent_id')
	def _check_unique_partner(self):
		for i in self:
			if i.vat and i.l10n_latam_identification_type_id:
				self.env.cr.execute("""update res_partner set vat = '%s' , l10n_latam_identification_type_id = %d where id = %d""" % (i.vat,i.l10n_latam_identification_type_id.id,i.id))
				self.env.cr.execute("""select vat from res_partner where vat = '%s' 
				and parent_id is null and l10n_latam_identification_type_id = %s""" % (str(i.vat),str(i.l10n_latam_identification_type_id.id)))
				res = self.env.cr.dictfetchall()
				if len(res) > 1:
					raise UserError("Ya existe un Partner con el mismo Tipo y Nro de Documento .")

	@api.onchange('name_p','last_name','m_last_name')
	def _get_complete_name(self):
		if not self.is_company:
			name = "%s %s %s"%(self.last_name,self.m_last_name,self.name_p)
			if name:
				name.replace(" ","")
				self.name = name

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		args = args or []
		einvoice_ids = []
		if name:
			einvoice_ids = self._search(['|',('name', '=', name),('vat','=',name)] + args, limit=limit, access_rights_uid=name_get_uid)
		if not einvoice_ids:
			einvoice_ids = self._search(['|',('name', operator, name),('vat', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
		return self.browse(einvoice_ids).name_get()

	@api.onchange('is_customer')
	def _customer_rank_one(self):
		for i in self:
			if i.is_customer:
				i._increase_rank_it('customer_rank')
			else:
				i._decrease_rank_it('customer_rank')

	@api.onchange('is_supplier')
	def _supplier_rank_one(self):
		for i in self:
			if i.is_supplier:
				i._increase_rank_it('supplier_rank')
			else:
				i._decrease_rank_it('supplier_rank')
	
	@api.model_create_multi
	def create(self, vals_list):
		search_partner_mode = self.env.context.get('res_partner_search_mode')
		is_customer = search_partner_mode == 'customer'
		is_supplier = search_partner_mode == 'supplier'
		if search_partner_mode:
			for vals in vals_list:
				if is_customer and 'customer_rank' not in vals:
					vals['is_customer'] = True
				elif is_supplier and 'supplier_rank' not in vals:
					vals['is_supplier'] = True
		return super().create(vals_list)