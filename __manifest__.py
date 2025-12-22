{
    'name': "Sistema Bordado",
    'summary': "Gestión de Pedidos con PDF y Asistencia",
    'author': "Wilmer Merchan",
    'depends': ['base', 'mrp', 'hr_attendance', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',               # <--- AQUÍ debe estar tu secuencia (ORD-001)
        'views/orden_pedido_view.xml',
        'views/jornada_view.xml',
        'views/incidencia_view.xml',
        
        # 'demo/demo.xml',             # <--- Déjalo comentado o vacío por ahora
    ],
    'application': True,
}