from odoo import models, fields

class IncidenciaBordado(models.Model):
    _name = 'bordado.incidencia'
    _description = 'Reporte de Fallas'
    _inherit = ['mail.thread']

    name = fields.Char(string="Código", default="Falla", readonly=True)
    maquina_id = fields.Many2one('mrp.workcenter', string="Máquina Afectada", required=True)
    tipo = fields.Selection([
        ('hilo', 'Rotura de Hilo'),
        ('aguja', 'Aguja Rota'),
        ('mecanica', 'Falla Mecánica'),
        ('limpieza', 'Limpieza')
    ], string="Tipo", required=True)
    nota = fields.Text("Detalles")
    state = fields.Selection([('nuevo', 'Reportado'), ('resuelto', 'Resuelto')], default='nuevo')

    def action_resolver(self):
        self.state = 'resuelto'