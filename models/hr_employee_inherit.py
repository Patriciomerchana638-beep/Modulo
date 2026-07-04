from odoo import models, fields, api
from datetime import timedelta
import base64

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def get_asistencia_semana_anterior(self):
        """
        Retorna las asistencias de este empleado correspondientes a la 
        SEMANA PASADA (Lunes a Domingo), para simular el reporte del lunes.
        """
        self.ensure_one()
        today = fields.Date.today()
        # Calcular el inicio de la semana pasada (Lunes)
        start_of_week = today - timedelta(days=today.weekday() + 7)
        # Calcular el fin de la semana pasada (Domingo)
        end_of_week = start_of_week + timedelta(days=6)

        # Buscamos los registros
        asistencias = self.env['hr.attendance'].search([
            ('employee_id', '=', self.id),
            ('check_in', '>=', start_of_week),
            ('check_in', '<=', end_of_week)
        ], order='check_in asc')
        
        return asistencias

    def get_total_horas_semana(self):
        """Suma las horas trabajadas de los registros encontrados"""
        recs = self.get_asistencia_semana_anterior()
        return sum(r.worked_hours for r in recs)
    
    @api.model
    def action_enviar_reporte_semanal_asistencia(self):
        """
        Esta función será llamada por el ROBOT (Cron) cada lunes.
        Genera el PDF masivo y lo envía por correo al Admin.
        """
        # 1. Buscar todos los empleados
        empleados = self.search([])
        
        if not empleados:
            return

        # 2. Generar el PDF en memoria
    
        pdf_content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'bordado_app.action_report_asistencia_semanal', 
            res_ids=empleados.ids
        )

        # 3. Crear el archivo adjunto en Odoo 
        nombre_archivo = f'Reporte_Asistencia_Semanal_{fields.Date.today()}.pdf'
        
        # AGREGAMOS .sudo() ANTES DE .create
        adjunto = self.env['ir.attachment'].sudo().create({
            'name': nombre_archivo,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'hr.employee',
            'res_id': empleados[0].id,
            'mimetype': 'application/pdf',
        })

       
        # Forzamos tu correo personal
        destinatario = 'merchana638@gmail.com'

        mail_values = {
            'subject': f'Reporte Semanal de Asistencia - {fields.Date.today()}',
            'body_html': f'''
                <p>Hola Administrador,</p>
                <p>El sistema ha generado automáticamente el reporte de asistencia de la semana anterior.</p>
                <p>Adjunto encontrarás el archivo PDF con el detalle de <b>{len(empleados)} empleados</b>.</p>
                <p>Saludos,<br/>Tu Sistema Odoo 🤖</p>
            ''',
            'email_to': destinatario,
            'attachment_ids': [(4, adjunto.id)],
        }
        
        self.env['mail.mail'].sudo().create(mail_values).send()