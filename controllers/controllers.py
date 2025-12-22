# from odoo import http


# class BordadoApp(http.Controller):
#     @http.route('/bordado_app/bordado_app', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bordado_app/bordado_app/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bordado_app.listing', {
#             'root': '/bordado_app/bordado_app',
#             'objects': http.request.env['bordado_app.bordado_app'].search([]),
#         })

#     @http.route('/bordado_app/bordado_app/objects/<model("bordado_app.bordado_app"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bordado_app.object', {
#             'object': obj
#         })

