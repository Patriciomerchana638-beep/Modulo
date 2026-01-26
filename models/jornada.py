from odoo import models, fields, api
from odoo.exceptions import UserError

class ControlAsistencia(models.TransientModel):
    _name = 'bordado.control.asistencia'
    _description = 'Panel de Control de Asistencia'

    employee_id = fields.Many2one('hr.employee', string="Empleado", readonly=True)
    nombre_empleado = fields.Char(related='employee_id.name', string="Nombre")
    foto = fields.Binary(related='employee_id.image_1920', readonly=True)
    
    esta_trabajando = fields.Boolean(default=False)
    hora_entrada = fields.Datetime(string="Hora de Entrada")
    horas_trabajadas = fields.Char(string="Tiempo Transcurrido", compute="_compute_tiempo")

    @api.model
    def default_get(self, fields_list):
        res = super(ControlAsistencia, self).default_get(fields_list)
        # Buscamos el empleado del usuario actual
        empleado = self.env.user.employee_id
        if not empleado:
            # Si eres Admin a veces no tienes empleado, esto evita el error
            return res 
        
        # Buscamos si tiene una asistencia abierta (sin check_out)
        asistencia = self.env['hr.attendance'].search([
            ('employee_id', '=', empleado.id),
            ('check_out', '=', False)
        ], limit=1)

        res.update({
            'employee_id': empleado.id,
            'esta_trabajando': bool(asistencia),
            'hora_entrada': asistencia.check_in if asistencia else False,
        })
        return res

    @api.depends('hora_entrada')
    def _compute_tiempo(self):
        for record in self:
            if record.hora_entrada:
                delta = fields.Datetime.now() - record.hora_entrada
                total_seconds = int(delta.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                record.horas_trabajadas = f"{hours:02} horas y {minutes:02} minutos"
            else:
                record.horas_trabajadas = "00:00"

    def action_iniciar_jornada(self):
        
        # Si ya tiene asistencia abierta, NO creamos otra, solo recargamos.
        asistencia_abierta = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee_id.id),
            ('check_out', '=', False)
        ], limit=1)
        
        if asistencia_abierta:
            return self._recargar_vista()

        # Si no hay abierta, ahora sí creamos
        self.env['hr.attendance'].create({
            'employee_id': self.employee_id.id,
            'check_in': fields.Datetime.now()
        })
        return self._recargar_vista()

    def action_finalizar_jornada(self):
        asistencia = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee_id.id),
            ('check_out', '=', False)
        ], limit=1)
        
        if asistencia:
            asistencia.check_out = fields.Datetime.now()
        
        return self._recargar_vista()

    def _recargar_vista(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bordado.control.asistencia',
            'view_mode': 'form',
            'target': 'current',  # Importante: current, no inline
            'res_id': self.create({}).id,
        }
    
    def _compute_display_name(self):
        for record in self:
            
            # saludo personalizado
            if record.nombre_empleado:
                record.display_name = f"👋 Hola, {record.nombre_empleado}"
            else:
                record.display_name = "👋 Hola, Usuario"