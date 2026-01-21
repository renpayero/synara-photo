# FotoApp - Módulo de Gestión y Venta de Fotografías

Módulo de Odoo para la gestión de fotógrafos, eventos, álbumes y venta de fotos digitales.

## Resumen

**Autor:** HC Sinergia | **Licencia:** AGPL-3 | **Categoría:** Sales

FotoApp permite a fotógrafos profesionales gestionar eventos, subir fotos con marca de agua automática, y vender imágenes digitales a través de una plataforma integrada con Odoo y Mercado Pago.

---

## Dependencias Principales

`base`, `product`, `account`, `website`, `website_sale`, `portal`, `mail`, `crm`, `payment_mercado_pago`, `subscription_oca`

---

## Arquitectura de Modelos

### Modelos Core

| Modelo | Descripción |
|--------|-------------|
| `fotoapp.plan` | Planes de suscripción (freemium, mensual, etc.) con límites de fotos, comisiones y productos asociados |
| `fotoapp.debt` | Gestión de deudas del fotógrafo (comisiones, suscripciones pendientes) |
| `sale.subscription` | Suscripciones activas de fotógrafos (extendido) |

### Modelos de Contenido

| Modelo | Descripción |
|--------|-------------|
| `tienda.foto.evento` | Eventos fotográficos (bodas, deportes, etc.) con estados: borrador → publicado → archivado |
| `tienda.foto.album` | Álbumes y colecciones de fotos, pueden ser privados o públicos |
| `tienda.foto.asset` | Fotos individuales con watermark automático, ciclo de vida y producto de venta |
| `tienda.foto.categoria` | Categorías de eventos (deportes, sociales, etc.) |

### Modelos Extendidos

| Modelo | Extensiones |
|--------|-------------|
| `res.partner` | Campos de fotógrafo (bio, watermark, tokens MP, métricas, plan activo) |
| `sale.order` | Comisiones FotoApp, links de descarga, tokens de validez |
| `payment.transaction` | Integración con deudas y comisiones |

---

## Controladores Web

| Controlador | Rutas Principales |
|-------------|-------------------|
| `gallery.py` | `/fotoapp/gallery`, `/fotoapp/category/<slug>`, `/fotoapp/event/<slug>` |
| `checkout_guest.py` | Flujo de compra sin registro para invitados |
| `photographer_dashboard.py` | Dashboard del fotógrafo con métricas |
| `photographer_events.py` | CRUD de eventos desde el portal |
| `photographer_albums.py` | Gestión de álbumes |
| `photographer_debts.py` | Visualización y pago de deudas |
| `photographer_settings.py` | Configuración del perfil y watermark |
| `plan.py` | Selección y cambio de planes |
| `download.py` | Descarga de fotos originales (sin watermark) |
| `order_portal.py` | Portal de pedidos del cliente |

---

## Características Principales

### Sistema de Suscripciones
- Planes configurables con límites de fotos publicadas
- Plan Freemium automático al registrarse
- Integración con `subscription_oca` para facturación recurrente
- Comisiones porcentuales sobre ventas

### Gestión de Fotos
- Upload masivo con watermark automático (texto o imagen)
- Ciclo de vida configurable: publicación → archivo → eliminación
- Generación automática de productos para venta

### Ventas y Pagos
- Integración Mercado Pago (OAuth, tokens de refresh)
- Checkout para invitados sin registro
- Generación de tokens de descarga con expiración
- Cálculo automático de comisiones por fotógrafo

### Portal del Fotógrafo
- Dashboard con métricas (ventas, fotos, comisiones)
- Gestión de eventos, álbumes y fotos
- Visualización de deudas pendientes
- Configuración de watermark personalizado

---

## Datos XML

- `fotoapp_plan_data.xml` - Planes de suscripción predefinidos
- `fotoapp_category_data.xml` - Categorías de eventos
- `fotoapp_debt_data.xml` - Productos para facturación de deudas
- `ir_cron_fotoapp_lifecycle.xml` - Cron para ciclo de vida de fotos
- `fotoapp_commission_cron.xml` - Cron para cálculo de comisiones

---

## Estructura de Directorios

```
fotoapp/
├── controllers/     # 16 archivos - Rutas web y API
├── models/          # 20 archivos - Lógica de negocio
├── views/           # 18 archivos - Templates y vistas backend
├── data/            # 8 archivos - Datos iniciales y crons
├── security/        # Permisos de acceso
├── static/          # Assets CSS/JS
└── tests/           # Tests del módulo
```
