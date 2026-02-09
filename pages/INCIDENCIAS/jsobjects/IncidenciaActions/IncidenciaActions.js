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

                const clienteNombre = clientesMap[item["account-id"]] || "Desconocido";
                const desc = item.description || "";
                const pipes = desc.split(" | ");
                const numeroAveria = pipes.length > 0 ? pipes[0].trim() : "";

                let emplazamiento = "";
                let descripcionProblema = "";

                if (numeroAveria.startsWith("ES")) {
                    // === ISTOBAL ===
                    // "ES00538724 | 5637193446 - ESTACION SERVICIO GUIBE S L - RIVAS | C/.FUNDICION, 53 - 28522 | Revision ITV"
                    // pipes[0] = ES00538724 (numero averia)
                    // pipes[1] = 5637193446 - ESTACION SERVICIO GUIBE S L - RIVAS (nº contrato + gasolinera)
                    // pipes[2] = C/.FUNDICION, 53 - 28522 (dirección)
                    // pipes[3+] = Revision ITV (problema)

                    let gasolinera = "";
                    if (pipes.length >= 2) {
                        const seg = pipes[1].trim().split(" - ");
                        // Primer segmento es el nº contrato, el resto es el nombre de la gasolinera
                        gasolinera = seg.slice(1).join(" - ").trim();
                    }
                    let direccion = "";
                    if (pipes.length >= 3) {
                        direccion = pipes[2].trim();
                    }
                    // Emplazamiento = gasolinera + dirección
                    emplazamiento = [gasolinera, direccion].filter(x => x).join(", ");

                    if (pipes.length >= 4) {
                        descripcionProblema = pipes.slice(3).join(" | ").trim();
                    }
                } else {
                    // === WASHTEC ===
                    // "413216055 | CAMPSA E.S.AREA LA ATALAYA M.D. - 161741240 48H Boquillas partidas"
                    // pipes[0] = 413216055 (numero averia)
                    // pipes[1] = CAMPSA E.S.AREA LA ATALAYA M.D. - descripcion problema

                    if (pipes.length >= 2) {
                        const seg = pipes[1].trim().split(" - ");
                        emplazamiento = seg[0].trim();
                        descripcionProblema = seg.slice(1).join(" - ").trim();
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