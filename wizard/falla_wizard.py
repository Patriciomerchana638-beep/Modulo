from odoo import models, fields, api

class BordadoFallaWizard(models.TransientModel):
    _name = 'bordado.falla.wizard'
    _description = 'Asistente para Reportar Fallas'

    orden_id = fields.Many2one('bordado.orden', string="Orden", readonly=True)

    # El timestamp exacto de la falla viene desde orden_pedido.py via context.
    # Se usa como hora_inicio de la incidencia para eliminar el desfase temporal.
    hora_inicio_falla = fields.Datetime(string="Hora de Inicio de Falla", readonly=True)

    tipo = fields.Selection([
        ('hilo', 'Rotura de Hilo'),
        ('aguja', 'Aguja Rota'),
        ('mecanica', 'Falla Mecánica'),
        ('limpieza', 'Limpieza Obligatoria'),
        ('espera', 'Espera de Material'),
        ('otro', 'Otro'),
    ], string="Causa", required=True)

    nota = fields.Text(string="Observaciones", required=True)

    def action_confirmar_falla(self):
        """
        Registra la causa de la falla en bordado.incidencia usando el timestamp
        exacto del momento en que el operario pulsó 'Reportar Falla', no el momento
        de confirmación del wizard. Esto garantiza consistencia con bordado.actividad.
        """
        hora_inicio = self.hora_inicio_falla or fields.Datetime.now()

        self.env['bordado.incidencia'].create({
            'orden_id': self.orden_id.id,
            'tipo': self.tipo,
            'nota': self.nota,
            'hora_inicio': hora_inicio,
        })

        return {'type': 'ir.actions.act_window_close'}