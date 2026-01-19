# FotoApp

FotoApp es el módulo de Synara para gestionar fotógrafos, galerías, planes de suscripción y ventas de fotos dentro de Odoo. Combina una tienda web con un portal especializado, integra cobros con Mercado Pago y raspa la lógica necesaria para llevar el ciclo de vida completo de la foto desde la publicación hasta la liquidación.

## Requisitos
- Odoo 18 con los módulos base listados en `__manifest__.py` (`website_sale`, `portal`, `mail`, `crm`, `payment_mercado_pago`, `subscription_oca`, entre otros).
- Planes, productos y plantillas de suscripción definidos por este módulo (se sincronizan automáticamente en `FotoappPlan`).
- Configuración de Mercado Pago y AFIP disponible en Ajustes > FotoApp (los parámetros están en `models/res_config_settings.py`).

## Componentes principales

### Modelos clave
- `fotoapp.plan` (models/plan.py): representa los planes públicos, sincroniza productos/plantillas, fija límites de fotos, álbumes, almacenamiento, comisiones y cargos iniciales.
- `sale.subscription` extendido (models/plan_subscription.py): controla suscripciones de fotógrafos, métricas de uso, límites, generación de deudas y cron jobs de facturación/autosuspensión.
- `res.partner` (models/res_partner.py): convierte partners en fotógrafos activos, almacena datos de pago, métricas, marca de agua y conexión con Mercado Pago; garantiza el plan freemium cuando no hay suscripción activa.
- `fotoapp.debt` (models/debt.py): registra obligaciones de suscripción o comisión, genera facturas automáticas, registra pagos y expira deudas vencidas.
- `sale.order` y `payment.transaction` (models/sale_order.py, models/payment_transaction.py): separan compras por fotógrafo, calculan comisiones/plataforma, generan tokens de descarga y enriquecen las transacciones de Mercado Pago con meta información y comisiones a cobrar al fotógrafo.
- `payment.provider` (models/payment_provider.py): ajusta los headers para permitir que los pagos del marketplace se firmen con el token de cada fotógrafo.

### Controladores principales
- `PhotographerPortalMixin` (controllers/portal_base.py) y `PhotographerDashboardController` (controllers/photographer_dashboard.py): aseguran el acceso al portal y calculan estadísticas/almacenamiento para el dashboard `[GET /mi/fotoapp]`.
- `FotoappManualPaymentController` (controllers/manual_payment.py): ofrece una vista estática con datos bancarios/Whatsapp del fotógrafo cuando un cliente elige pago manual.
- `FotoappDownloadController` (controllers/download.py): expone `/fotoapp/public_download/<token>` para generar un ZIP con las fotos asociadas a un pedido confirmado.
- Hay controladores adicionales para galerías, eventos, órdenes y espacios de pago de invitados dentro de `controllers/*`.

### Vistas y assets
- `views/*.xml`: definen la landing pública, galerías, bloc de planes, portal del fotógrafo, checkout de invitados, órdenes y paneles de deuda.
- `static/src/js/payment_guest_email.js`: mejora el formulario de checkout para envíos de email cuando se paga como invitado.

## Flujos centrales
1. **Venta y suscripción**: un cliente compra un producto asociado a `fotoapp.plan`; `sale.order` crea o renueva la suscripción del fotógrafo y recalcula comisiones. `plan._ensure_plan_products()` mantiene la coherencia entre planes, productos y plantillas.
2. **Cobros y comisiones**: la transacción de Mercado Pago se enriquece con el fotógrafo/comisión; el proveedor agrega el header `Authorization` con el token del fotógrafo conectado (modelo `res.partner.mp_*`). Las deudas se registran en `fotoapp.debt`, se facturan automáticamente y se enlazan con pagos.
3. **Portal del fotógrafo**: el portal listado en `/mi/fotoapp` muestra eventos recientes, límites de almacenamiento y métricas en pantalla; la foto y los álbumes se vinculan a la suscripción activa para controlar límites.
4. **Descargas**: luego de confirmar el pedido, se genera un token (`download_token`) y se envía un correo con el link `/fotoapp/public_download/<token>` para descargar el ZIP.
5. **Pagos manuales y requerimientos legales**: el checkout permite mostrar los datos bancarios de cada fotógrafo para transferencias; también se almacenan datos fiscales y certificados AFIP para emitir facturas.

## Datos maestros y tareas programadas
- `data/fotoapp_plan_data.xml`: planes base publicados en la web.
- `data/fotoapp_category_data.xml`: categorías de fotos/álbumes para la galería pública.
- `data/fotoapp_debt_data.xml`: plantillas de deuda/comisiones iniciales.
- `data/fotoapp_subscription_template.xml`: blueprint usado para clonar plantillas de suscripción por plan.
- `data/ir_cron_fotoapp_lifecycle.xml`: cron jobs que generan deudas periódicas, marcan suscripciones en gracia y limpian referencias. Estos crons llaman a los métodos `fotoapp_cron_*` de `SaleSubscription` y `FotoappDebt`.
- `hooks.post_init_hook` (hooks.py): se ejecuta al instalar el módulo para sincronizar productos/plantillas y migrar suscripciones heredadas.

## Configuración
1. Ir a Ajustes > Configuración > FotoApp y completar los parámetros de Mercado Pago (`fotoapp_mp_*`) y AFIP (`fotoapp_afip_*`).
2. Establecer el diario de cobros de Mercado Pago para registrar pagos automáticos (`fotoapp_mp_gateway_journal_id`).
3. Subir certificados AFIP si se factura en Argentina.
4. Verificar que el plan freemium (`code=FREEMIUM`) exista; si no, se recomienda crear uno para onboarding automático.
5. Cada fotógrafo debe conectar Mercado Pago en su ficha para poder procesar pagos marketplace (ver campos `mp_*` en res.partner).

## Pruebas y verificaciones
- `tests/test_photo_lifecycle.py`: usa los registros de miembros y flujos de ciclo de vida para validar que las suscripciones, órdenes y descargas evolucionan correctamente.

## Notas adicionales
- El módulo asume que los fotógrafos son partners (`is_photographer=True`) y automáticamente les asigna un plan freemium si no tienen uno activo.
- Las imágenes originales se almacenan en `tienda.foto.asset` y se empaquetan vía `zipfile` en el controlador de descargas.
- Los límites de almacenamiento se calculan en bytes para evitar overflow y se exponen en los informes del portal y del plan.
- Cada pedido genera un token de descarga con vencimiento de 30 días; el link solo funciona si el pedido está confirmado y el token no venció.
- Para contextualizar comisiones, cada `sale.order` y `payment.transaction` guarda los importes destinados al fotógrafo y a la plataforma.
