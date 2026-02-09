export default {
    async sincronizarProveedoresMasivo() {
        let registroInicial = 0;
        let tamanoBloque = 500; // Traer todos de una vez (son ~303)
        let continuar = true;

        try {
            while (continuar) {
                const data = await get_proveedores_stel.run({
                    start: registroInicial,
                    limit: tamanoBloque
                });

                if (!data || !Array.isArray(data) || data.length === 0) {
                    console.log("Sincronización finalizada: No hay más registros.");
                    continuar = false;
                    break;
                }

                try {
                    await q_importar_masivo_proveedores.run({
                        json_data: JSON.stringify(data)
                    });
                    console.log(`Sincronizados ${data.length} registros desde el ${registroInicial}`);
                } catch (dbErr) {
                    console.error(`Error en bloque ${registroInicial}:`, dbErr.message);
                }

                // Si recibimos menos del bloque solicitado, ya no hay más
                if (data.length < tamanoBloque) {
                    console.log("Último bloque recibido, fin de sincronización.");
                    continuar = false;
                    break;
                }

                registroInicial += tamanoBloque;

                // Pausa de cortesía para la API
                await new Promise(r => setTimeout(r, 800));
            }

            showAlert("Sincronización masiva de proveedores terminada con éxito", "success");
            await Select_public_proveedores.run();

        } catch (e) {
            showAlert("Error crítico: " + e.message, "error");
        }
    }
}
