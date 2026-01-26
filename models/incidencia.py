from odoo import models, fields, api

class IncidenciaBordado(models.Model):
    _name = 'bordado.incidencia'
    _description = 'Reporte de Fallas y Paradas'

    # Relación: Una incidencia pertenece a una Orden
    orden_id = fields.Many2one('bordado.orden', string="Orden Vinculada")
    duracion = fields.Float(string="Duración (min)", compute="_compute_duracion", store=True)
    
    tipo = fields.Selection([
        ('hilo', 'Rotura de Hilo'),
        ('aguja', 'Aguja Rota'),
        ('mecanica', 'Falla Mecánica'),
        ('limpieza', 'Limpieza Obligatoria'),
        ('espera', 'Espera de Material')
    ], string="Causa", required=True)
    
    nota = fields.Text("Observaciones")
    hora_inicio = fields.Datetime(default=fields.Datetime.now)
    hora_fin = fields.Datetime(string="Hora Reinicio")

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_duracion(self):
        for record in self:
            if record.hora_inicio and record.hora_fin:
                # Restamos fin - inicio
                delta = record.hora_fin - record.hora_inicio
                # Convertimos segundos a minutos
                record.duracion = delta.total_seconds() / 60
            else:
                record.duracion = 0.0



    