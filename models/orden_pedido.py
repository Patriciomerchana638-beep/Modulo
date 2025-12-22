# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OrdenPedido(models.Model):
    _name = 'bordado.orden'
    _description = 'Orden de Producción (Tesis)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Encabezado
    name = fields.Char(string='Código', required=True, copy=False, readonly=True, default='Nuevo')
    cliente = fields.Char(string='Cliente', required=True)
    fecha = fields.Date(string='Fecha', default=fields.Date.today)
    
    # EL REEMPLAZO DEL COLOR: PDF
    archivo_pdf = fields.Binary(string="Detalle Pedido (PDF)", attachment=True, required=True)
    nombre_archivo = fields.Char(string="Nombre del Archivo")

    # Asignación
    maquina_id = fields.Many2one('mrp.workcenter', string="Máquina (Ej: 6B)", required=True)
    operario_id = fields.Many2one('res.users', string="Operador", default=lambda self: self.env.user)

    # Estados del Proceso
    state = fields.Selection([
        ('borrador', '📋 Revisando Orden'),
        ('preparacion', '🧵 Buscando Materiales (15min)'),
        ('produccion', '⚙️ Bordando'),
        ('finalizado', '✅ Terminado')
    ], string='Estado', default='borrador', tracking=True)

    # Botones
    def action_preparar(self):
        self.state = 'preparacion'

    def action_bordar(self):
        self.state = 'produccion'

    def action_finalizar(self):
        self.state = 'finalizado'

    # Secuencia Automática (ORD-001)
    # ---------------------------------------------------------
    # CORRECCIÓN PARA ODOO 19: USAR api.model_create_multi
    # ---------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Genera la secuencia ORD-001 automáticamente"""
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('bordado.orden') or 'Nuevo'
        return super(OrdenPedido, self).create(vals_list)
