export default {
  // onPageLoad: Se ejecuta al cargar la página
  onLoad: async () => {
    // Initial cleanup
    await storeValue('localLines', []);

    // 1. Gestionar Modo Edición y Parametros desde URL
    const mode = appsmith.URL.queryParams.mode;

    // Reset defaults
    await storeValue('defaultClientId', '');
    await storeValue('defaultTitle', '');

    if (mode === 'EDIT' || mode === 'NEW') {
      await storeValue('editando', true);

      // LOGICA PARA NUEVO ALBARAN DESDE INCIDENCIA
      if (mode === 'NEW') {
        // 1. Titulo
        if (appsmith.URL.queryParams.titulo) {
          await storeValue('defaultTitle', appsmith.URL.queryParams.titulo);
        }

        // 2. Cliente (Buscar ID por nombre si viene nombre)
        if (appsmith.URL.queryParams.cliente_nombre) {
          // Aseguramos que tenemos clientes cargados
          const clientes = await q_selector_clientes.run();
          if (clientes) {
            const nombreBuscado = appsmith.URL.queryParams.cliente_nombre.toLowerCase();
            // Busqueda aproximada o exacta
            const found = clientes.find(c => c.nombre_fiscal && c.nombre_fiscal.toLowerCase().includes(nombreBuscado));
            if (found) {
              await storeValue('defaultClientId', found.id_stel.toString());
              showAlert(`Cliente pre-seleccionado: ${found.nombre_fiscal}`, "success");
            } else {
              showAlert(`No se encontró cliente con nombre: ${appsmith.URL.queryParams.cliente_nombre}`, "warning");
            }
          }
        }
      }

    } else {
      await storeValue('editando', false);
    }

    // 2. Inicializar Precios si es necesario (espera a que existan datos)
    // Usamos un pequeño delay o comprobación para asegurar que q_ficha_cabecera tiene datos
    if (appsmith.URL.queryParams.id) {
      await LogicaPrecios.inicializarLineasServicio();
    }
  },

  guardarAlbaran: async () => {
    // 1. Bloqueo de seguridad para no guardar doble
    if (appsmith.store.guardando) return;
    await storeValue("guardando", true);

    try {
      const ref = appsmith.URL.queryParams.ref || appsmith.URL.queryParams.referencia;

      // 2. Lanzamos la actualización a la base de datos
      const mode = appsmith.URL.queryParams.mode;
      const esNuevo = (mode === 'NEW');

      let resultado;

      if (esNuevo) {
        // Lógica de CREACIÓN
        const newId = Date.now(); // ID Temporal
        const newRef = "TEMP-" + newId;

        await q_insert_albaran.run({
          id: newId,
          referencia: newRef,
          titulo: Input_TITULO.text || appsmith.store.defaultTitle || "Nuevo Albarán",
          cliente_id: Select_public_clientes2.selectedOptionValue || appsmith.store.defaultClientId || null,
          ref_incidencia: appsmith.URL.queryParams.ref_incidencia || ""
        });

        resultado = { affectedRows: 1 }; // Simulado

        // Redirigir a modo edición con el nuevo ID
        showAlert("Albarán creado con éxito. Redirigiendo...", "success");
        navigateTo('ALBARANES FICHA', { id: newId, mode: 'EDIT' }, 'SAME_WINDOW');
        return;

      } else {
        // Lógica de ACTUALIZACIÓN (existente)
        const ref = appsmith.URL.queryParams.ref || appsmith.URL.queryParams.referencia;
        resultado = await q_update_albaran.run();

        if (resultado.affectedRows === 0) {
          showAlert("¡Atención! No se ha encontrado el albarán con referencia: " + ref, "error");
          return;
        }

        showAlert("Albarán actualizado con éxito ✅", "success");
        await storeValue("editando", false);
      }

      // ❌ HEMOS QUITADO EL 'navigateTo'.
      // Ahora te quedarás en la misma pantalla, viendo tus cambios guardados y la tabla bonita.

    } catch (err) {
      showAlert("Error técnico: " + err.message, "error");
    } finally {
      // 4. Liberamos el botón para poder volver a usarlo si hace falta
      await storeValue("guardando", false);
    }
  }
}