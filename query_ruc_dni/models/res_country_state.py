from odoo import models, fields, api
from odoo.exceptions import UserError
import requests


class Provinicias(models.Model):
    _inherit = 'res.country.state'
    synchro = fields.Boolean(string='Sincronizado')

    def unlink(self):
        # "your code"
        is_materia = self.env['res.users'].has_group('query_ruc_dni.group_delete_provincias')

        for record in self:
            if not is_materia and record.synchro:
                raise UserError('No tiene permiso para eliminar una provincia sincronizada')
        return super(Provinicias, self).unlink()


    '''

    def create(self,values):
        # "your code"
        is_materia = self.env['res.users'].has_group('query_ruc_dni.group_delete_provincias')

        if not is_materia or is_materia == False:
            raise UserError('No tiene permiso para esta accion')

        return super(Provinicias, self).create(values)
    '''

    def write(self,fields):
        # "your code"
        is_materia = self.env['res.users'].has_group('query_ruc_dni.group_delete_provincias')
        for record in self:
            if not is_materia and record.synchro:
                raise UserError('No tiene permiso para editar una provincia sincronizada')
        return super(Provinicias, self).write(fields)

    def synchro_provincias(self):
        is_materia = self.env['res.users'].has_group('query_ruc_dni.group_delete_provincias')
        if (not is_materia or is_materia == False):
            raise UserError('No tiene permiso para Syncronizar')
        #hacer un get

        url = "https://itgrupo.net/ubigeos_publish_js_it/static/src/ubigeos.json"
        PARAMS = {}
        r = requests.get(url=url, params=PARAMS)
        data = r.json()
        #ubigeo
        for record in self:
            for d in data:
                '''
                if int(d['id_ubigeo']) == 1312:
                    if str(d['ubigeo_inei']).strip() == str(record.code).strip():
                        raise ValueError('hola')
                    raise UserError(d['ubigeo_inei'])
                '''

                if str(d['ubigeo_inei']).strip() == str(record.code).strip():
                    #raise UserError(d['ubigeo_inei'])
                    #buscar departamento
                    departamento = self.env['res.country.state'].search([('code','=',d['departamento_inei']),('country_id.code','=','PE')])

                    if departamento:
                        record.state_id = departamento.id
                        record.state_id.name =  str(d['departamento'])
                        record.state_id.synchro = True
                    else:
                        raise UserError('no se encontro el departamento para '+str(d['departamento_inei']))

                    provincia =  self.env['res.country.state'].search([('code','=',d['provincia_inei'])])
                    if provincia:
                        record.province_id = provincia.id
                        if not record.province_id.state_id.id == departamento.id:
                            record.province_id.state_id = departamento.id
                        record.province_id.name = str(d['provincia'])
                        record.province_id.synchro = True
                    else:
                        raise UserError('no se encontro la provincia para '+str(d['provincia_inei']))
                    record.synchro = True
                    record.name =  str(d['distrito'])


    def desmarcar_provincias(self):

        is_materia = self.env['res.users'].has_group('query_ruc_dni.group_delete_provincias')
        if (not is_materia or is_materia == False):
            raise UserError('No tiene permiso para Syncronizar')
        for record in self:
            record.synchro = False