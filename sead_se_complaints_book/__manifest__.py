# -*- coding: utf-8 -*-
# complaints_book
{
    'name': 'Helpdesk - Libro de reclamaciones',
    'version': '1.0',
    'category': 'Operations/Helpdesk',
    'sequence': 58,
    'summary': 'Libro de reclamaciones',
    'website': 'https://sead.pe',
    'depends': [
        'helpdesk',
    ],
    'data': [
        'views/helpdesk_ticket_view_form_inherit.xml',
        'views/mail_template.xml'

    ],
    "installable": True,
}
