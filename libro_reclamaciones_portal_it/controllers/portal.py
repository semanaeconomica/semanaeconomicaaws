# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class LibroReclamacionesPortal(http.Controller):

    @http.route('/libro-reclamaciones', type='http', auth='public', website=True, csrf=False)
    def libro_reclamaciones_form(self, **kwargs):

        return request.render('libro_reclamaciones_portal_it.libro_reclamaciones_form_template', {
            'values': {},
        })

    @http.route('/libro-reclamaciones/submit', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def libro_reclamaciones_submit(self, **post):
        try:
            required_fields = ['nombre_completo', 'correo_electronico', 'dni_ruc', 
                             'domicilio', 'telefono', 'tipo', 'bien_contratado']
            
            if post.get('es_menor_edad'):
                required_fields.extend(['representante_nombre', 'representante_correo', 
                                      'representante_telefono', 'representante_domicilio'])
            
            missing_fields = []
            for field in required_fields:
                if not post.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                error_msg = 'Por favor complete todos los campos obligatorios.'
                if post.get('es_menor_edad'):
                    error_msg = 'Por favor complete todos los campos obligatorios. Los datos del representante son requeridos para menores de edad.'
                return request.render('libro_reclamaciones_portal_it.libro_reclamaciones_form_template', {
                    'error': error_msg,
                    'values': post
                })
            
            values = {
                'nombre_completo': post.get('nombre_completo'),
                'correo_electronico': post.get('correo_electronico'),
                'dni_ruc': post.get('dni_ruc'),
                'domicilio': post.get('domicilio'),
                'telefono': post.get('telefono'),
                'tipo': post.get('tipo'),
                'bien_contratado': post.get('bien_contratado'),
                'descripcion': post.get('descripcion', ''),
                'state': 'enviado',
                'es_menor_edad': bool(post.get('es_menor_edad')),
            }
            
            if post.get('es_menor_edad'):
                values.update({
                    'representante_nombre': post.get('representante_nombre', ''),
                    'representante_correo': post.get('representante_correo', ''),
                    'representante_telefono': post.get('representante_telefono', ''),
                    'representante_domicilio': post.get('representante_domicilio', ''),
                })
            
            libro_reclamaciones = request.env['libro.reclamaciones'].sudo().create(values)
            
            _logger.info('Nuevo reclamo creado: %s - %s', libro_reclamaciones.numero_reclamo, libro_reclamaciones.nombre_completo)
            
            return request.render('libro_reclamaciones_portal_it.libro_reclamaciones_success_template', {
                'numero_reclamo': libro_reclamaciones.numero_reclamo,
                'nombre': libro_reclamaciones.nombre_completo,
            })
            
        except Exception as e:
            _logger.error('Error al crear reclamo: %s', str(e))
            return request.render('libro_reclamaciones_portal_it.libro_reclamaciones_form_template', {
                'error': 'Ocurrió un error al enviar el reclamo. Por favor intente nuevamente.',
                'values': post
            })

