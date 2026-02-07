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

            // 2. Obtener Clientes
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

            // 3. Obtener Incidencias de STEL
            await API_Get_Incidencias.run();
            const items = API_Get_Incidencias.data;

            if (!items || items.length === 0) {
                showAlert("⚠️ No se encontraron incidencias.", "warning");
                this.loading = false;
                return;
            }

            // 4. Parsear y guardar
            let count = 0;
            for (const item of items) {
                const statusName = statesMap[item["incident-state-id"]] || item["incident-state-id"] || "Desconocido";
                if (!item.id) continue;

                const clienteNombre = clientesMap[item["account-id"]] || "Desconocido";
                const desc = item.description || "";
                const pipes = desc.split(" | ");
                const numeroAveria = pipes.length > 0 ? pipes[0].trim() : "";

                let emplazamiento = "";
                let modelo = "";
                let descripcionProblema = "";

                if (numeroAveria.startsWith("ES") && pipes.length >= 3) {
                    // === ISTOBAL ===
                    // pipes[0] = ES00543477
                    // pipes[1] = 5637193446 - ESTACION SERVICIO GUIBE S L - RIVAS
                    // pipes[2] = C/.FUNDICION, 53 - CENTRO LAVAMANIA
                    // pipes[3] = Modelo 4PH2500, ...M18 - Tubería rota por la parte superior

                    // Emplazamiento = gasolinera + dirección (pipes[1] sin nº parte + pipes[2])
                    const seg1 = pipes[1].trim().split(" - ");
                    const gasolinera = seg1.slice(1).join(" - ").trim();
                    const direccion = pipes[2].trim();
                    emplazamiento = gasolinera + ", " + direccion;

                    // Modelo y descripción del problema (pipes[3+])
                    if (pipes.length >= 4) {
                        const resto = pipes.slice(3).join(" | ").trim();
                        const lastDash = resto.lastIndexOf(" - ");
                        if (lastDash > 0) {
                            modelo = resto.substring(0, lastDash).trim();
                            descripcionProblema = resto.substring(lastDash + 3).trim();
                        } else {
                            descripcionProblema = resto;
                        }
                    }
                } else {
                    // === WASHTEC ===
                    // pipes[0] = 413223167
                    // pipes[1] = CAMPSA E.S.AREA Sº LA ATALAYA M.D. - 161741240 48H ... Boquillas partidas

                    if (pipes.length >= 2) {
                        const firstDash = pipes[1].trim().indexOf(" - ");
                        if (firstDash > 0) {
                            emplazamiento = pipes[1].trim().substring(0, firstDash).trim();
                            descripcionProblema = pipes[1].trim().substring(firstDash + 3).trim();
                        } else {
                            emplazamiento = pipes[1].trim();
                        }
                    }
                }

                // Guardar: descripcion = "averia\nemplazamiento\nmodelo\ndescripcion"
                const datosExtra = [numeroAveria, emplazamiento, modelo, descripcionProblema].join("\n");

                await Query_Upsert_Incidencia.run({
                    id: item.id,
                    fecha: item["creation-date"],
                    cliente: clienteNombre,
                    asunto: item["full-reference"] || "Sin Ref",
                    descripcion: datosExtra,
                    estado: statusName,
                    direccion: emplazamiento,
                    prioridad: item.priority || "Normal",
                    cliente_id: item["account-id"]
                });
                count++;
            }

            showAlert("✅ " + count + " incidencias sincronizadas.", "success");
            await Get_Staging.run();

        } catch (error) {
            showAlert("❌ Error sync: " + error.toString(), "error");
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
            const clienteNombre = row.cliente;
            if (!clienteId && clienteNombre) {
                const clienteData = await Query_Find_Client_ID.run({ nombre: clienteNombre });
                if (clienteData && clienteData.length > 0) {
                    clienteId = clienteData[0].id_stel;
                }
            }
            const incidentRef = row.referencia || row.numero_actividad;
            const newId = Date.now();
            await Query_Insert_New_Albaran.run({
                id_stel: newId,
                referencia: nextRef,
                titulo: incidentRef + " - " + (row.emplazamiento || ""),
                cliente_id: clienteId,
                ref_incidencia: incidentRef
            });
            showAlert("✅ Albarán creado. Redirigiendo...", "success");
            navigateTo("ALBARANES FICHA", { id: newId, mode: "EDIT" }, "SAME_WINDOW");
        } catch (error) {
            showAlert("❌ Error: " + error.message, "error");
        }
    },

    setupTable: async () => {
        try {
            await Query_Create_Incidencias.run();
            showAlert("Tabla Incidencias lista.", "success");
        } catch (e) {
            showAlert("Error: " + e.message, "error");
        }
    }
}