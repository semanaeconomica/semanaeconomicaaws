# -*- coding: utf-8 -*-
from odoo import fields, models, api


class LibroReclamaciones(models.Model):
    _name = 'libro.reclamaciones'
    _description = 'Libro de Reclamaciones'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'nombre_completo'

    nombre_completo = fields.Char(
        string='Nombre Completo',
        required=True,
        help='Nombre completo del reclamante'
    )
    
    correo_electronico = fields.Char(
        string='Correo Electrónico',
        required=True,
        help='Correo electrónico del reclamante'
    )
    
    dni_ruc = fields.Char(
        string='DNI o RUC o CE',
        required=True,
        help='Documento de identidad o RUC del reclamante'
    )
    
    domicilio = fields.Char(
        string='Domicilio',
        required=True,
        help='Dirección del reclamante'
    )
    
    telefono = fields.Char(
        string='Teléfono',
        required=True,
        help='Teléfono de contacto'
    )
    
    es_menor_edad = fields.Boolean(
        string='Es menor de edad',
        default=False,
        help='Indica si la persona que presenta el reclamo es menor de edad'
    )
    
    representante_nombre = fields.Char(
        string='Nombre del Representante',
        help='Nombre completo del padre, madre o representante legal'
    )
    
    representante_correo = fields.Char(
        string='Correo del Representante',
        help='Correo electrónico del representante'
    )
    
    representante_telefono = fields.Char(
        string='Teléfono del Representante',
        help='Teléfono de contacto del representante'
    )
    
    representante_domicilio = fields.Char(
        string='Domicilio del Representante',
        help='Dirección del representante'
    )
    
    tipo = fields.Selection([
        ('reclamo', 'Reclamo'),
        ('otro', 'Otro')
    ], string='Tipo', required=True, default='reclamo',
       help='Tipo de registro: Reclamo u otro')
    
    bien_contratado = fields.Selection([
        ('producto', 'Producto'),
        ('servicio', 'Servicio')
    ], string='Bien Contratado', required=True,
       help='Indica si el reclamo es sobre un producto o servicio')
    
    descripcion = fields.Text(
        string='Descripción del Reclamo',
        help='Detalles del reclamo o consulta'
    )
    
    create_date = fields.Datetime(
        string='Fecha de Creación',
        readonly=True
    )
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
        ('cancelado', 'Cancelado')
    ], string='Estado', default='enviado', readonly=True, tracking=True)
    
    respuesta = fields.Text(
        string='Respuesta',
        help='Respuesta al reclamo'
    )
    
    numero_reclamo = fields.Char(
        string='Número de Reclamo',
        readonly=True,
        copy=False,
        help='Número único del reclamo'
    )

    @api.model
    def create(self, vals):

        if not vals.get('numero_reclamo'):
            vals['numero_reclamo'] = self.env['ir.sequence'].next_by_code('libro.reclamaciones') or 'New'
        return super(LibroReclamaciones, self).create(vals)

