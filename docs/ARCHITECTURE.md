# Arquitectura y decisiones (Fase 1)

## Estilo
Monolito modular por dominios (`app/modules/<dominio>/{models,schemas,repository,service,router,dependencies,tasks}.py`).
Los módulos solo se comunican mediante servicios o eventos de dominio, nunca importando repositorios ajenos.

## Decisiones clave
| Tema | Decisión | Motivo |
|---|---|---|
| Acceso a BD | SQLAlchemy 2.0 **síncrono** + psycopg 3 | Mismo código en API y Celery; `SELECT … FOR UPDATE` y transacciones más simples de razonar. FastAPI ejecuta endpoints `def` en threadpool. |
| Multiempresa | `organization_id` en toda tabla de negocio; el contexto (organización/sede) sale del token + `UserRole`, nunca de parámetros del cliente. Repositorios reciben un `TenantContext`. Se evaluará RLS de PostgreSQL como defensa adicional en Fase 3. | Aislamiento verificable con pruebas. |
| Datos por nivel | Organización: usuarios, roles, pacientes, catálogos, facturación. Clínica: citas, atenciones, planes. Sede: consultorios, caja, stock. | Un paciente pertenece a la organización y puede atenderse en varias sedes. |
| Citas sin doble reserva | Restricción `EXCLUDE USING gist` (extensión `btree_gist`) sobre `(dentist_id, tstzrange(starts_at, ends_at))` y `(room_id, …)` para estados activos. | La garantía vive en PostgreSQL, no solo en Python. |
| Fechas | `timestamptz` en UTC; API en ISO 8601 con offset; presentación `America/Lima`. Fechas sin zona se rechazan. | Evita ambigüedades. |
| Dinero | `Numeric(12,2)` + `Decimal`; precios copiados al detalle. | Sin `float`. |
| Sesiones | JWT de acceso corto (15 min) + refresh token opaco almacenado como hash en BD, con rotación y revocación. Argon2 para contraseñas. | Revocación real. |
| Recordatorios | Tabla de trabajos con clave única `(cita, tipo, instante)`; Celery Beat escanea periódicamente y encola. Sin timers de días en Redis. | Sobrevive a reinicios; sin duplicados. |
| Tiempo real | Redis Pub/Sub entre procesos; mensajes solo con IDs/tipo de evento, sin datos clínicos. Notificaciones persistidas en PostgreSQL. | Escala a varias instancias. |
| Errores | Formato único `{"error": {code, message, request_id, details?}}`; sin eco de valores recibidos. | Evita fugas de datos personales. |
| Normativa | Los códigos de la NTS 188 (odontograma), NTS 139, Ley 29733 y su reglamento y los requisitos SUNAT **se verificarán contra los textos oficiales** antes de fijar catálogos (Fases 5–6). Nada se declara “conforme” sin esa verificación. | Evitar afirmaciones legales infundadas. |

## Estructura planificada
```
app/core/        config, logging, errores, tiempo, celery_app   (Fase 1)
app/db/          Base, sesión, mixins                            (Fase 2)
app/security/    hashing, JWT, permisos                          (Fase 3)
app/modules/     dominios                                        (Fases 3–9)
migrations/      Alembic                                         (Fase 2)
```
