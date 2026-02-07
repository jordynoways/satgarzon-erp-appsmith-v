export default {
    loading: false,

    sync: async () => {
        this.loading = true;
        try {
            // 1. Obtener Estados
            const statesData = await get_incident_states.run();
            const statesMap = {};
            if (Array.isArray(statesData)) {
                statesData.forEach(s => {
                    const id = s["incident-state-id"] || s.id;
                    const name = s["incident-state-name"] || s.name || s.nombre;
                    if (id) statesMap[id] = name;
                });
            }

            // 2. Obtener Clientes para mapear ID -> Nombre real
            await get_clientes.run();
            const clientesData = get_clientes.data;
            const clientesMap = {};
            if (Array.isArray(clientesData)) {
                clientesData.forEach(c => {
                    const id = c.id || c["account-id"];
                    const name = c["legal-name"] || c["commercial-name"] || c.name || c.nombre;
                    if (id) clientesMap[id] = name;
                });
            }

            // 3. Obtener TODAS las Incidencias de STEL
            await API_Get_Incidencias.run();
            const items = API_Get_Incidencias.data;

            if (!items || items.length === 0) {
                showAlert("⚠️ No se encontraron incidencias.", "warning");
                this.loading = false;
                return;
            }

            // 4. Guardar en Postgres
            let count = 0;
            for (const item of items) {
                const statusName = statesMap[item["incident-state-id"]] || item["incident-state-id"] || "Desconocido";

                if (!item.id) continue;

                // Nombre real del cliente desde STEL (ej: ISTOBAL ESPAÑA S.L.U)
                const desc = item.description || "";
                const parts = desc.split(" | ");
                const clienteNombre = clientesMap[item["account-id"]] ||
                    (parts.length > 1 ? parts.slice(1).join(" | ").split(" - ")[0].trim() : "Desconocido");

                // Extraer ubicación/emplazamiento de la descripción
                // Formato: "ES00538724 | 5637193446 - ESTACION SERVICIO GUIBE S L - RIVAS | C/.FUNDICION, 53..."
                // O: "413216055 | Flow Car Global Alcobendas - cortar y tensar cadena"
                let emplazamiento = "";
                if (parts.length > 1) {
                    const locationPart = parts[1].trim();
                    // Coger nombre del emplazamiento (antes del último segmento que suele ser la descripción)
                    const segments = locationPart.split(" - ");
                    if (segments.length >= 2) {
                        // Tomamos los primeros segmentos como ubicación
                        emplazamiento = segments.slice(0, Math.min(segments.length, 2)).join(" - ").trim();
                    } else {
                        emplazamiento = locationPart;
                    }
                }

                await Query_Upsert_Incidencia.run({
                    id: item.id,
                    fecha: item["creation-date"],
                    cliente: clienteNombre,
                    asunto: item["full-reference"] || "Sin Ref",
                    descripcion: desc,
                    estado: statusName,
                    direccion: emplazamiento,
                    prioridad: item.priority || "Normal",
                    cliente_id: item["account-id"]
                });
                count++;
            }

            showAlert(`✅ ${count} incidencias sincronizadas.`, "success");
            await Get_Staging.run();

        } catch (error) {
            showAlert("❌ Error sync incidencias: " + error.toString(), "error");
        } finally {
            this.loading = false;
        }
    },

    irAAlbaran: async (row) => {
        if (!row) {
            showAlert("No se seleccionó incidencia", "warning");
            return;
        }

        try {
            const refData = await Query_Get_Next_Albaran_Ref.run();
            const nextRef = refData[0].siguiente_ref;

            let clienteId = row.cliente_id_stel;
            const clienteNombre = row.cliente || row.fabricante;

            if (!clienteId && clienteNombre) {
                const clienteData = await Query_Find_Client_ID.run({ nombre: clienteNombre });
                if (clienteData && clienteData.length > 0) {
                    clienteId = clienteData[0].id_stel;
                }
            }

            if (!clienteId) {
                showAlert(`⚠️ No se encontró cliente '${clienteNombre}' en STEL.`, "warning");
            }

            const incidentRef = row.referencia || row.numero_actividad || row.numero_averia;
            const newId = Date.now();

            await Query_Insert_New_Albaran.run({
                id_stel: newId,
                referencia: nextRef,
                titulo: `${incidentRef} - ${row.emplazamiento || ''}`,
                cliente_id: clienteId,
                ref_incidencia: incidentRef
            });

            showAlert("✅ Albarán creado. Redirigiendo...", "success");

            navigateTo('ALBARANES FICHA', {
                id: newId,
                mode: 'EDIT'
            }, 'SAME_WINDOW');

        } catch (error) {
            showAlert("❌ Error creando albarán: " + error.message, "error");
        }
    },

    setupTable: async () => {
        try {
            await Query_Create_Incidencias.run();
            showAlert("Tabla Incidencias lista.", "success");
        } catch (e) {
            showAlert("Error setup tabla: " + e.message, "error");
        }
    }
}