from odoo import models, fields, api

class ActividadBordado(models.Model):
    _name = 'bordado.actividad'
    _description = 'Registro detallado de tiempos y operarios'

    orden_id = fields.Many2one('bordado.orden', string="Orden")
    
    # IMPORTANTE: Aquí guardamos quién hizo ESTA parte del trabajo
    user_id = fields.Many2one('res.users', string="Operario", default=lambda self: self.env.user, readonly=True)
    
    # Quitamos cualquier default aquí, lo controlaremos con la función de abajo
    numero_puesta = fields.Integer(string="N° Puesta")
    
    # --- AQUÍ ESTÁ LA ACTUALIZACIÓN (Se agregó Limpieza) ---
    tipo_actividad = fields.Selection([
        ('preparacion', ' Cambio / Preparación'),
        ('bordado', ' Bordando'),
        ('costura', ' Costura'), 
        ('pausa', 'Pausa por Prioridad'),
        ('falla', ' Falla Técnica'),
        ('limpieza', ' Corte de Hilos')  
    ], string="Actividad", required=True)

    inicio = fields.Datetime(default=fields.Datetime.now, string="Inicio")
    fin = fields.Datetime(string="Fin")
    duracion = fields.Float(string="Minutos", compute="_compute_duracion", store=True)
    maquina_id = fields.Many2one('mrp.workcenter', string="Máquina")

    # --- LÓGICA ACTUALIZADA ---
    @api.onchange('tipo_actividad')
    def _onchange_tipo_actividad(self):
        """
        Si selecciona 'Bordado': Calcula el siguiente número de puesta (1, 2, 3...).
        Si es Limpieza, Costura o Pausa: Pone el número de puesta en 0.
        """
        if self.tipo_actividad == 'bordado':
            # Si hay una orden asociada, contamos cuántos bordados lleva
            if self.orden_id:
                # Filtramos las actividades que ya existen y son de tipo 'bordado'
                bordados_existentes = self.orden_id.actividad_ids.filtered(lambda a: a.tipo_actividad == 'bordado')
                # El nuevo número es la cantidad existente + 1 (la actual)
                self.numero_puesta = len(bordados_existentes) + 1
            else:
                self.numero_puesta = 1
        else:
            # Si es Limpieza, Costura, Preparación o Pausa, no aplica número de puesta
            self.numero_puesta = 0

    @api.depends('inicio', 'fin')
    def _compute_duracion(self):
        for record in self:
            if record.inicio and record.fin:
                delta = record.fin - record.inicio
                record.duracion = delta.total_seconds() / 60
            else:
                record.duracion = 0.0