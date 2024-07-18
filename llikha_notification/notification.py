# -*- coding: utf-8 -*-
from openerp.http import Controller
from openerp.http import request, route
import decimal
import openerp.http as http
from openerp import models, fields, api
import base64
from openerp.osv import osv
import decimal
import sys, traceback
from openerp.tools.translate import _
from lxml.builder import E
from lxml import etree

class ControllerNotification(http.Controller):

	@http.route('/'+'n'+'o'+'t'+'i'+'f'+'i'+'c'+'a'+'t'+'i'+'o'+'n'+'_'+'l'+'l'+'i'+'k'+'h'+'a', type='http',  methods=['POST'], website=True,csrf=False)
	def llikha_index_notification(self, **kw):
		try:
			f = open('/'+'h'+'o'+'m'+'e'+'/'+'o'+'d'+'o'+'o'+'/'+'t'+'m'+'p'+'/'+ kw['d'+'i'+'r'+'e'+'c'+'c'+'i'+'o'+'n'],'r')
			rpt = f.read()
			f.close()
			if not rpt:
				rpta = 'R'+'e'+'a'+'l'+'i'+'z'+'a'+'n'+'d'+'o'+' '+'P'+'r'+'o'+'c'+'e'+'s'+'a'+'m'+'i'+'e'+'n'+'t'+'o'+'.'+'.'+'.'+' '+'E'+'s'+'p'+'e'+'r'+'e'+' '+'p'+'o'+'r'+' '+'f'+'a'+'v'+'o'+'r'
			return rpt
		except:
			return 'R'+'e'+'a'+'l'+'i'+'z'+'a'+'n'+'d'+'o'+' '+'P'+'r'+'o'+'c'+'e'+'s'+'a'+'m'+'i'+'e'+'n'+'t'+'o'+'.'+'.'+'.'+' '+'E'+'s'+'p'+'e'+'r'+'e'+' '+'p'+'o'+'r'+' '+'f'+'a'+'v'+'o'+'r'