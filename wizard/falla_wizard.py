# UBICACIÓN: wizard/falla_wizard.py
from odoo import models, fields, api

class BordadoFallaWizard(models.TransientModel):
    _name = 'bordado.falla.wizard'
    _description = 'Asistente para Reportar Fallas'

    orden_id = fields.Many2one('bordado.orden', string="Orden", readonly=True)
    
    # Usamos los mismos campos que tu modelo de Incidencia
    tipo = fields.Selection([
        ('hilo', 'Rotura de Hilo'),
        ('aguja', 'Aguja Rota'),
        ('mecanica', 'Falla Mecánica'),
        ('limpieza', 'Limpieza Obligatoria'),
        ('espera', 'Espera de Material'),
        ('otro', 'Otro')
    ], string="Causa", required=True)
    
    nota = fields.Text(string="Observaciones", required=True)

    def action_confirmar_falla(self):
        """
        Guarda la incidencia en el historial y cierra la ventana.
        El tiempo ya se está contando en 'orden_pedido.py', así que aquí solo registramos la causa.
        """
        # Creamos el registro en TU tabla de historial
        self.env['bordado.incidencia'].create({
            'orden_id': self.orden_id.id,
            'tipo': self.tipo,
            'nota': self.nota,
            'hora_inicio': fields.Datetime.now(),
            # 'state': 'abierta' # Importante para saber cual cerrar luego
        })
        
        return {'type': 'ir.actions.act_window_close'}