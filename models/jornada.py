from odoo import models, fields, api
from odoo.exceptions import UserError

class JornadaLaboral(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def registrar_asistencia_rapida(self):
        # 1. Verificar que el usuario tenga un empleado ligado
        empleado = self.env.user.employee_id
        if not empleado:
            raise UserError("Tu usuario no tiene un Empleado vinculado. Avisa al Gerente.")

        # 2. Buscar si tiene asistencia abierta (sin hora de salida)
        asistencia_abierta = self.search([
            ('employee_id', '=', empleado.id),
            ('check_out', '=', False)
        ], limit=1)

        # Variables para el mensaje
        mensaje = ""
        titulo = ""
        tipo_mensaje = ""

        if asistencia_abierta:
            # MARCAR SALIDA (Cerrar jornada)
            asistencia_abierta.check_out = fields.Datetime.now()
            titulo = "👋 HASTA MAÑANA"
            mensaje = "Jornada cerrada correctamente."
            tipo_mensaje = "warning"
        else:
            # MARCAR ENTRADA (Iniciar jornada)
            self.create({'employee_id': empleado.id, 'check_in': fields.Datetime.now()})
            titulo = "☀️ BIENVENIDO"
            mensaje = "Jornada iniciada. ¡Buen turno!"
            tipo_mensaje = "success"

        # 3. REDIRECCIÓN AL DASHBOARD (KANBAN)
        # Esto hace que tras marcar, te lleve a ver las órdenes
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tablero de Producción',
            'res_model': 'bordado.orden',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'context': {'search_default_my_orders': 1}, 
            'params': {
                'title': titulo,
                'message': mensaje,
                'type': tipo_mensaje,
                'sticky': False,
            }
        }