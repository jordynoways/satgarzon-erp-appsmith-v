---
description: Reglas para trabajar con Appsmith Git Sync sin romper el merge
---

# Reglas de Appsmith + Git Sync

## ⚠️ REGLA PRINCIPAL
**NUNCA crear archivos nuevos de queries, datasources o jsobjects directamente en el repo Git.**
Estos archivos SIEMPRE los debe generar Appsmith desde su UI.

## ✅ Lo que SÍ se puede editar en Git
- Modificar contenido de archivos existentes (body de query, código JS, propiedades de widgets)
- Código de infraestructura (`infra/`, scripts, etc.)
- Archivos `.txt` de queries (el SQL o body)

## ❌ Lo que NUNCA crear en Git
- Nuevos `metadata.json` de queries
- Nuevos `datasources/*.json`
- Nuevos `jsobjects/*/metadata.json`
- Nuevas páginas (el `PAGINA.json`)

## 🖥️ Cómo crear componentes nuevos en Appsmith
1. Abrir Appsmith en el navegador: `http://192.168.1.226:80`
2. Crear la query/datasource/JSObject **desde la interfaz de Appsmith**
3. Hacer commit desde Appsmith (Git Sync → Commit)
4. Pull en el repo local para traer los cambios
5. Si hay que ajustar contenido, editar el archivo existente en Git
6. Push + Pull desde Appsmith

## 🔧 Si se rompe el merge (procedimiento de emergencia)
1. SSH al servidor: `ssh garzon@192.168.1.226` (password: jordy)
2. El repo Git interno de Appsmith está en:
   `/appsmith-stacks/git-storage/6962c0bfdca6af427460bc1d/6987b6eefc080202ca7dfe57/satgarzon-erp-appsmith-v`
3. Crear un git bundle desde el repo local:
   `git bundle create master.bundle master`
4. Copiar al servidor:
   `scp master.bundle garzon@192.168.1.226:/tmp/master.bundle`
5. Copiar al contenedor y resetear:
   ```bash
   docker cp /tmp/master.bundle appsmith:/tmp/master.bundle
   docker exec appsmith bash -c 'cd /appsmith-stacks/git-storage/6962c0bfdca6af427460bc1d/6987b6eefc080202ca7dfe57/satgarzon-erp-appsmith-v && export GIT_PAGER=cat && git fetch /tmp/master.bundle master:refs/remotes/origin/master && git reset --hard origin/master'
   ```
6. Probar Pull desde Appsmith

## 📝 Notas técnicas
- Appsmith usa `DEFAULT_REST_DATASOURCE` para APIs REST sin datasource dedicado
- Las URLs van completas en el campo `path` (ej: `http://192.168.1.226:8100/analizar-pedido`)
- Los `gitSyncId` los genera Appsmith internamente, no se pueden inventar
- Contenedor Docker de Appsmith: `appsmith` (imagen: `appsmith/appsmith-ce:latest`)
