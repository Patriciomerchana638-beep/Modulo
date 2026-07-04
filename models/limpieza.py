from odoo import models, fields, api


class BordadoLimpieza(models.Model):
    _name = 'bordado.limpieza'
    _description = 'Registro de Limpieza de Máquinas'
    _order = 'fecha desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string="Nombre",
        compute='_compute_name',
        store=True,
    )
    maquina_id = fields.Many2one(
        'mrp.workcenter',
        string="Máquina",
        required=True,
        ondelete='restrict',
    )
    fecha = fields.Date(
        string="Fecha",
        default=fields.Date.today,
        required=True,
    )
    operario_ids = fields.Many2many(
        'hr.employee.public',
        'bordado_limpieza_hr_employee_rel',
        'limpieza_id',
        'employee_id',
        string="Operarios Asignados",
    )
    inicio = fields.Datetime(string="Inicio")
    fin = fields.Datetime(string="Fin")
    duracion = fields.Float(
        string="Duración (min)",
        compute='_compute_duracion',
        store=True,
    )
    observaciones = fields.Text(string="Observaciones")
    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('finalizado', 'Finalizado'),
    ], string="Estado", default='pendiente', required=True)

    @api.depends('maquina_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"Limpieza {rec.maquina_id.name}" if rec.maquina_id else "Limpieza"

    @api.depends('inicio', 'fin')
    def _compute_duracion(self):
        for rec in self:
            if rec.inicio and rec.fin:
                rec.duracion = (rec.fin - rec.inicio).total_seconds() / 60
            else:
                rec.duracion = 0.0

    def action_abrir_wizard_inicio(self):
        self.ensure_one()
        return {
            'name': 'Iniciar Limpieza',
            'type': 'ir.actions.act_window',
            'res_model': 'bordado.limpieza.inicio.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_limpieza_id': self.id},
        }

    def action_abrir_wizard_fin(self):
        self.ensure_one()
        return {
            'name': 'Finalizar Limpieza',
            'type': 'ir.actions.act_window',
            'res_model': 'bordado.limpieza.fin.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_limpieza_id': self.id},
        }
