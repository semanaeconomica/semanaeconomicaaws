from odoo import fields, models , api
import requests

class Modulos(models.Model):
    _inherit = 'ir.module.module'
    check_url_it = fields.Boolean(compute="get_check_url")
    def get_check_url(self):
        valid = False
        #buscar url
        url = self.env['ir.config_parameter'].search([('key','=','web.base.url')])
        url_main = self.env['ir.config_parameter'].search([('key', '=', 'url_main')])
        url_it = self.env['ir.config_parameter'].search([('key', '=', 'url_itgroup')])
        url_valid = self.env['ir.config_parameter'].search([('key', '=', 'url_validated')])

        headers = {"Accept": "application/json", "Content-Type": "application/json"}



        if url and url_main and url_it and url_valid:
            if 1 == 1 :
            #if url_valid.value == 'False':
                url = url.value
                url_main = url_main.value
                #if 1 == 1:
                try:
                    data = {
                        'url': url,
                        'url_main': url_main
                    }
                    r = requests.post(url=url_it.value, json=data, headers=headers)
                    r = r.json()
                    if 'result' in r:
                        if r['result']:
                            if r['result'] in ['production', 'test']:
                                #raise ValueError(r)
                                valid = True
                                url_valid.value = 'True'
                            else:
                                url_valid.value = 'False'
                        else:
                            raise ValueError(r)
                    else:
                        raise ValueError([data,url_it.value,r])

                except:
                    valid = False
            #else:
            #    raise ValueError(url_valid.value)


        for record in self:
            record.check_url_it = valid