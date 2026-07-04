from odoo import models, api, _
from odoo.exceptions import UserError


def validar_solo_admin(env):
    """
    Función independiente para verificar si el usuario es Administrador.
    Cualquier clase en este archivo puede usarla.
    """
    if not env.user.has_group('base.group_system'):
        raise UserError(_(
            "🛑 ACCIÓN DENEGADA 🛑\n\n"
            "No tienes permiso para ELIMINAR este registro.\n"
            "Solo el ADMINISTRADOR puede borrar datos críticos de la fábrica.\n"
            "Contacta a Gerencia si cometiste un error."
        ))


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def unlink(self):
        validar_solo_admin(self.env)  #  Usamos la función global
        return super(HrAttendance, self).unlink()

    def write(self, vals):
        # Administrador 
        if self.env.user.has_group('base.group_system'):
            return super(HrAttendance, self).write(vals)
        
        # Operario
        if 'check_in' in vals:
            raise UserError(_("🛑 No puedes cambiar la hora de entrada."))
        if 'check_out' in vals:
            for record in self:
                if record.check_out:
                    raise UserError(_("🛑 Este registro ya está cerrado."))
        return super(HrAttendance, self).write(vals)


class BordadoOrden(models.Model):
    _inherit = 'bordado.orden'

    def unlink(self):
        validar_solo_admin(self.env) 
        return super(BordadoOrden, self).unlink()


class BordadoActividad(models.Model):
    _inherit = 'bordado.actividad'

    def unlink(self):
        validar_solo_admin(self.env)  
        return super(BordadoActividad, self).unlink()


class BordadoIncidencia(models.Model):
    _inherit = 'bordado.incidencia'

    def unlink(self):
        validar_solo_admin(self.env)  
        return super(BordadoIncidencia, self).unlink()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def unlink(self):
        validar_solo_admin(self.env)  
        return super(HrEmployee, self).unlink()