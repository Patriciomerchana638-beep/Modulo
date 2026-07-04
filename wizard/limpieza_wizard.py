from odoo import models, fields, api


class BordadoLimpiezaInicioWizard(models.TransientModel):
    _name = 'bordado.limpieza.inicio.wizard'
    _description = 'Asistente de Inicio de Limpieza'

    limpieza_id = fields.Many2one('bordado.limpieza', readonly=True)
    maquina_nombre = fields.Char(
        related='limpieza_id.maquina_id.name',
        string="Máquina",
        readonly=True,
    )
    # Tabla de relación explícita para no colisionar con bordado.limpieza.operario_ids
    # El filtrado por turno activo se hace en default_get con sudo() para evitar
    # el AccessError sobre hr.employee.public en usuarios sin permisos de RRHH.
    operario_ids = fields.Many2many(
        'hr.employee.public',
        'bordado_limpieza_inicio_wiz_emp_rel',
        'wizard_id',
        'employee_id',
        string="Operarios en Turno",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'operario_ids' in fields_list:
            # Buscar asistencias activas (sin check_out) con sudo() para evitar
            # restricciones de acceso sobre hr.attendance en perfiles de operario.
            active_attendances = self.env['hr.attendance'].sudo().search([
                ('check_out', '=', False),
            ])
            employee_ids = active_attendances.mapped('employee_id').ids
            if employee_ids:
                res['operario_ids'] = [(6, 0, employee_ids)]
        return res

    def action_confirmar_inicio(self):
        self.ensure_one()
        self.limpieza_id.sudo().write({
            'inicio': fields.Datetime.now(),
            'state': 'en_proceso',
            'operario_ids': [(6, 0, self.operario_ids.ids)],
        })
        return {'type': 'ir.actions.act_window_close'}


class BordadoLimpiezaFinWizard(models.TransientModel):
    _name = 'bordado.limpieza.fin.wizard'
    _description = 'Asistente de Finalización de Limpieza'

    limpieza_id = fields.Many2one('bordado.limpieza', readonly=True)
    maquina_nombre = fields.Char(
        related='limpieza_id.maquina_id.name',
        string="Máquina",
        readonly=True,
    )
    inicio_info = fields.Datetime(
        related='limpieza_id.inicio',
        string="Inicio Registrado",
        readonly=True,
    )
    observaciones = fields.Text(string="Observaciones de la Limpieza", required=True)

    def action_confirmar_fin(self):
        self.ensure_one()
        self.limpieza_id.sudo().write({
            'fin': fields.Datetime.now(),
            'state': 'finalizado',
            'observaciones': self.observaciones,
        })
        return {'type': 'ir.actions.act_window_close'}
