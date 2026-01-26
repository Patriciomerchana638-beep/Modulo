{
    'name': "Sistema Bordado",
    'summary': "Control de Proceso",
    'author': "Wilmer Merchan",
    'depends': ['base', 'mrp', 'hr_attendance', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/cron_jobs.xml',
        'views/orden_pedido_view.xml',
        'views/jornada_view.xml',
        'views/incidencia_view.xml',
        'views/reporte_view.xml',
        'views/ocultar_menus.xml',
        'reports/orden_report.xml',
        'reports/asistencia_report.xml',
        'views/falla_wizard_view.xml',
    ],  # <--- Aquí se cierra la lista de datos. ¡No borres esta coma!

    'license': 'LGPL-3',  # <--- La licencia va AQUÍ FUERA (hermana de 'data')

    # 'demo/demo.xml',
    'application': True,
}
