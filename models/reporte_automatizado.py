from odoo import models, fields, api
from datetime import timedelta
import base64

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def action_enviar_reporte_semanal_asistencia(self):
        """ Envía un resumen de asistencia al Administrador todos los lunes """
        
        # 1. Definir fechas (Semana anterior)
        hoy = fields.Date.today()
        inicio = hoy - timedelta(days=7)
        fin = hoy - timedelta(days=1)
        
        # 2. Buscar registros
        asistencias = self.search([
            ('check_in', '>=', inicio),
            ('check_in', '<=', fin)
        ])
        
        if not asistencias:
            return # No enviar nada si no hay datos

        # 3. Generar PDF (Usando el reporte nativo de asistencia de Odoo)
        #  Si falla, podemos enviar solo texto.
        pdf_content, _ = self.env.ref('hr_attendance.hr_attendance_report_view_pivot')._render_qweb_pdf(asistencias.ids)
        
        adjunto = self.env['ir.attachment'].create({
            'name': f'Asistencias_{inicio}_al_{fin}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'hr.attendance',
            'mimetype': 'application/pdf',
        })

        # 4. Enviar Correo al Admin
        admin = self.env.ref('base.user_admin') # Usuario Admin principal
        if admin.email:
            self.env['mail.mail'].create({
                'subject': f'📅 Reporte Semanal de Asistencia ({inicio} - {fin})',
                'body_html': f'<p>Adjunto el reporte de {len(asistencias)} asistencias registradas.</p>',
                'email_to': admin.email,
                'attachment_ids': [(4, adjunto.id)]
            }).send()