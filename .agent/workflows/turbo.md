---
description: Ejecutar comandos en modo turbo (auto-aprobación)
---

// turbo-all

Cuando este workflow está activo, todos los comandos de terminal se ejecutan automáticamente sin pedir confirmación al usuario.

## Notas
- Aplica solo a comandos de terminal (run_command)
- Los comandos destructivos (borrar archivos, instalar paquetes del sistema) seguirán pidiendo confirmación por seguridad del agente
- Para activar, menciona "/turbo" en el chat
