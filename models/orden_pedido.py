# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OrdenPedido(models.Model):
    _name = 'bordado.orden'
    _description = 'Orden de Producción Avanzada'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    temp_inicio_costura = fields.Datetime(string="Temp Inicio Costura") # Campo temporal para control interno

    # datos de orden
    name = fields.Char(string='Código', required=True, copy=False)
    cliente = fields.Char(string='Cliente', required=True)
    fecha = fields.Date(default=fields.Date.today)
    puntadas = fields.Integer(string="Número de Puntadas", default=0, help="Cantidad total de puntadas del diseño.")
    fecha_fin = fields.Datetime(string="Fecha Finalización", readonly=True)
    
    maquina_id = fields.Many2one('mrp.workcenter', string="Máquina", required=False, tracking=True)
    imagen_diseno = fields.Image(string="Foto del Diseño", max_width=1024, max_height=1024, verify_resolution=True)
    
    # Operario Responsable
    operario_id = fields.Many2one('res.users', default=lambda self: self.env.user, string="Operario Actual")

    #  CHECKLIST Y PRIORIDAD 
    materiales_listos = fields.Boolean(string="✅ ¿Diseño, Hilos y Telas listos?", default=False)
    
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', '🔴 URGENTE')
    ], default='0', string="Prioridad", tracking=True)

    observacion_turno = fields.Html(string="Bitácora de Relevo", help="Notas para el siguiente turno")

    #  RELACIONES 
    incidencia_ids = fields.One2many('bordado.incidencia', 'orden_id', string="Historial de Paradas")
    actividad_ids = fields.One2many('bordado.actividad', 'orden_id', string="Bitácora de Tiempos")

    #  CONTROL DE PUESTAS
    puesta_actual = fields.Integer(string="Puesta Actual", default=1, readonly=True, tracking=True)
    
    sub_estado = fields.Selection([
        ('espera', 'Esperando Inicio'),
        ('preparando', '🔧 En Montaje / Cambio'),
        ('ejecutando', '🧵 Máquina Trabajando')
    ], default='espera', string="Estado de la Puesta")

    # ESTADOS GENERALES 
    state = fields.Selection([
        ('borrador', 'Revisando'),
        ('preparacion', 'Buscando Materiales'),
        ('costura', 'Costura'),
        ('produccion', 'BORDANDO'),
        ('detenido', 'DETENIDO (Incidencia/Pausa)'),
        ('limpieza', 'Corte de Hilos'),
        ('finalizado', 'Terminado')
    ], string='Estado', default='borrador', tracking=True)

  
    # LÓGICA (NOTIFICACIONES DE PRIORIDAD)
    
    def write(self, vals):
        """
        Detecta cuando el Admin cambia la prioridad (marca la estrella).
        """
        # Si están activando la prioridad (La estrella pasa a '1')
        if 'priority' in vals and vals['priority'] == '1':
            # Mandamos el aviso a los operarios en el Chatter
            self.message_post(
                body="🔥 ¡ATENCIÓN EQUIPO! - Esta orden ha sido marcada como PRIORIDAD ALTA.",
                message_type="comment",
                subtype_xmlid="mail.mt_comment"
            )
        return super(OrdenPedido, self).write(vals)

  
    # VISOR DE IMAGEN
    def action_ver_imagen(self):
        self.ensure_one()
        if not self.imagen_diseno:
            return {
                'type': 'ir.actions.client', 
                'tag': 'display_notification', 
                'params': {
                    'message': '⚠️ Primero debes subir una foto.', 
                    'type': 'warning',
                    'sticky': False,
                }
            }
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/image?model=bordado.orden&id={self.id}&field=imagen_diseno',
            'target': 'new',
        }

   
    # FLUJO DE ESTADOS
    
    def action_preparar(self):
        if self.state == 'costura':
            self._cerrar_actividad_abierta()
        self.state = 'preparacion'

    def action_verificar_inicio(self):
        self.operario_id = self.env.user 
        
        if self.materiales_listos:
            self.state = 'produccion'
            self.sub_estado = 'espera'
        else:
            self.state = 'costura' 
            self.env['bordado.actividad'].create({
                'orden_id': self.id,
                'numero_puesta': 0,
                'tipo_actividad': 'costura',
                'maquina_id': self.maquina_id.id,
                'user_id': self.env.user.id,
                'inicio': fields.Datetime.now()
            })
            self.message_post(body="⚠️ Materiales no listos. Iniciando registro de COSTURA.")

    #  CONTROL DE TIEMPOS (PUESTAS) 
    def action_iniciar_puesta_preparacion(self):
        self.operario_id = self.env.user 
        self.state = 'produccion'
        self.sub_estado = 'preparando'
        
        self.env['bordado.actividad'].create({
            'orden_id': self.id,
            'numero_puesta': self.puesta_actual,
            'tipo_actividad': 'preparacion',
            'maquina_id': self.maquina_id.id,
            'user_id': self.env.user.id
        })

    def action_arrancar_maquina(self):
        self.operario_id = self.env.user
        self._cerrar_actividad_abierta() # Cierra preparación

        self.sub_estado = 'ejecutando'
        self.env['bordado.actividad'].create({
            'orden_id': self.id,
            'numero_puesta': self.puesta_actual,
            'tipo_actividad': 'bordado',
            'maquina_id': self.maquina_id.id,
            'user_id': self.env.user.id
        })

    def action_finalizar_puesta(self):
        """Paso 3: Termina la puesta actual y PREPARA el contador para la siguiente"""
        
        # 1. Cerramos el cronómetro actual
        self._cerrar_actividad_abierta()
        
        # 2. Dejamos el mensaje con el número viejo (ej: "Puesta 1 finalizada")
        self.message_post(body=f"✅ Puesta {self.puesta_actual} finalizada.")

        # 3. Sumamos 1 al contador (Ahora vale 2)
        self.puesta_actual += 1

        # 4. Ponemos el estado en espera para que salga el botón de "Iniciar Montaje"
        self.sub_estado = 'espera'

    def action_siguiente_puesta(self):
        
        # 1.  Cierra cualquier actividad que haya quedado abierta (Bordado, Costura, etc.)
        self._cerrar_actividad_abierta()

        # 2. Dejamos constancia de que la puesta anterior se terminó (aunque sea forzada)
        self.message_post(body=f"⏩ Salto Rápido: Puesta {self.puesta_actual} finalizada manualmente.")

        # 3. Ahora sí, sumamos 1 al contador
        self.puesta_actual += 1

        # 4. Iniciamos automáticamente la preparación de la nueva
        self.action_iniciar_puesta_preparacion()


    

    
    # 1. REPORTAR FALLA 
 
    def action_reportar_falla(self):
        
        self.ensure_one()
        
        # PASO 1: Detenemos el reloj de lo que se estaba haciendo (Bordado/Preparación)
        self._cerrar_actividad_abierta()
        
        # PASO 2: Cambiamo estado visual
        self.state = 'detenido'
        
        #  Iniciamos el cronómetro de "Tiempo Muerto"
        # Usamos 'pausa' para que el sistema sepa que es tiempo improductivo
        self.env['bordado.actividad'].create({
            'orden_id': self.id,
            'numero_puesta': self.puesta_actual,
            'tipo_actividad': 'falla', 
            'maquina_id': self.maquina_id.id,
            'user_id': self.env.user.id,
            'inicio': fields.Datetime.now()
        })
        
        # PASO 4: Mensaje en el panel de chatter
        self.message_post(
            body="MÁQUINA DETENIDA POR FALLA TÉCNICA - Cronómetro de parada iniciado.",
            message_type="comment",
            subtype_xmlid="mail.mt_comment"
        )
        
        # PASO 5: Abrimos la ventana (Wizard) para clasificar la falla
        return {
            'name': 'Reportar Falla Técnica',
            'type': 'ir.actions.act_window',
            'res_model': 'bordado.falla.wizard', 
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_orden_id': self.id}
        }


    # 2. PAUSA POR PRIORIDAD 
 
    def action_pausar_por_prioridad(self):
        """
        Pausa por orden administrativa (Urgencia/Prioridad).
        """
        self.ensure_one()
        
        # 1. Cerramos actividad anterior
        self._cerrar_actividad_abierta()
        self.state = 'detenido'
        
        # 2. Iniciamos el cronómetro de la pausa
        self.env['bordado.actividad'].create({
            'orden_id': self.id,
            'numero_puesta': self.puesta_actual,
            'tipo_actividad': 'pausa',
            'maquina_id': self.maquina_id.id,
            'user_id': self.env.user.id,
            'inicio': fields.Datetime.now()
        })

        # 3. Mensaje en el panel de chatter
        self.message_post(body="⏸️ Orden pausada por: PRIORIDAD ALTA.")

   
    # 3. REANUDAR (ACTUALIZADO PARA CERRAR INCIDENCIAS)
   
    def action_reanudar(self):
        """
        Cierra tiempos, cierra incidencias abiertas y vuelve a trabajar.
        """
        for orden in self:
            # 1. Cierra el cronómetro de tiempo muerto (Pausa/Falla)
            orden._cerrar_actividad_abierta()

            # 2. Busca si hay una incidencia ABIERTA en el historial para cerrarla
            incidencia = self.env['bordado.incidencia'].search([
                ('orden_id', '=', orden.id),
                ('hora_fin', '=', False) # Busca la que no tenga hora fin
            ], limit=1)
            
            mensaje = "▶️ PAUSA FINALIZADA. Producción reanudada."
            
            # Si se encontra una incidencia abierta, la cerramos
            if incidencia:
                incidencia.write({'hora_fin': fields.Datetime.now()})
                mensaje = f"✅ Falla resuelta ({incidencia.tipo}). Retomando producción."

            # 3. Volvemos al estado de Producción
            orden.state = 'produccion'
            orden.sub_estado = 'ejecutando' # Asumimos que la máquina arranca
            
            # 4. Iniciamos el cronómetro PRODUCTIVO (Bordando)
            orden.env['bordado.actividad'].create({
                'orden_id': orden.id,
                'numero_puesta': orden.puesta_actual,
                'tipo_actividad': 'bordado', # Volvemos a sumar tiempo bueno
                'maquina_id': orden.maquina_id.id,
                'user_id': orden.env.user.id,
                'inicio': fields.Datetime.now()
            })
            
            # 5. Publicamos el mensaje correcto (Falla resuelta o Pausa fin)
            orden.message_post(body=mensaje)

  
    # finalizar orden sin limpieza
  
    def action_finalizar(self):
        """Cierra la orden directamente (camino normal)"""
        self.ensure_one()
        self._cerrar_actividad_abierta()
        self.state = 'finalizado'
        self.message_post(body="✅ Orden Finalizada (Sin registro de Corte de Hilos).")

  
    # finalizar orden con limpieza
    
    def action_pasar_a_limpieza(self):
        """Manda a limpieza opcional"""
        self.ensure_one()
        self._cerrar_actividad_abierta()
        
        self.state = 'limpieza'
        self.sub_estado = 'ejecutando' 

        # Iniciamos el cronómetro de la actividad de limpieza
        self.env['bordado.actividad'].create({
            'orden_id': self.id,
            'numero_puesta': 0,
            'tipo_actividad': 'limpieza', 
            'maquina_id': self.maquina_id.id,
            'user_id': self.env.user.id
        })
        self.message_post(body="🧼 Iniciando fase de Corte de Hilos.")


    # finalizar definitivamente la orden
    
    def action_terminar_definitivamente(self):
        """Cierra la orden después de limpiar"""
        self.ensure_one()
        self._cerrar_actividad_abierta()
        self.state = 'finalizado'
        self.fecha_fin = fields.Datetime.now()
        self.message_post(body="📦 Corte de Hilos terminada. Orden Finalizada.")

        
    # funcion auxiliar para cerrar actividades abiertas
    def _cerrar_actividad_abierta(self):
        """Busca cualquier actividad sin hora fin y la cierra"""
        actividad_abierta = self.actividad_ids.filtered(lambda a: not a.fin)
        if actividad_abierta:
            actividad_abierta.write({'fin': fields.Datetime.now()})


    

    # funcion de costura manual
    def action_ir_a_costura(self):
        self.ensure_one()
        self.state = 'costura'
        # Guardamos la hora exacta del clic
        self.temp_inicio_costura = fields.Datetime.now()
        self.message_post(body="⏸️ Iniciando labor de Costura Manual.")

    
    def action_retomar_produccion(self):
        self.ensure_one()
        
        # Verificamos si hay una hora de inicio guardada
        if self.temp_inicio_costura:
            hora_fin = fields.Datetime.now()
            
           
           
            self.env['bordado.actividad'].create({
                'orden_id': self.id,
                'user_id': self.env.user.id,
                'maquina_id': self.maquina_id.id,
                'tipo_actividad': 'costura', 
                'inicio': self.temp_inicio_costura,
                'fin': hora_fin,
                'numero_puesta': 0  # Costura no lleva número de puesta
            })
            
            # Limpiamos el campo temporal
            self.temp_inicio_costura = False

        # Volvemos al estado normal
        self.write({
            'state': 'produccion',
            'sub_estado': 'espera'
        })
        self.message_post(body="▶️ Fin de costura manual. Retomando a Bordado.") 


    # En models/orden_pedido.py

    def get_resumen_puestas(self):
        """
        Suma tiempos por puesta, PERO EXCLUYE LAS PAUSAS.
        """
        resumen = {}
        for linea in self.actividad_ids:
            # Condición estricta: Debe tener número de puesta Y NO SER PAUSA
            if linea.numero_puesta > 0 and linea.tipo_actividad != 'pausa':
                p = linea.numero_puesta
                if p not in resumen:
                    resumen[p] = 0.0
                resumen[p] += linea.duracion
        
        return sorted(resumen.items())

    def get_total_pausas(self):
        """
        Calcula solo el tiempo perdido en Pausas.
        """
        total_pausa = sum(line.duracion for line in self.actividad_ids if line.tipo_actividad == 'pausa')
        return total_pausa