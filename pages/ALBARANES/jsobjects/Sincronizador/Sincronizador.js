export default {
    manualSync: async () => {
        // 1. Llamamos a STEL
        const response = await update_albaranes_stel.run();
        
        if (!response || response.length === 0) {
            showAlert("No han llegado datos de STEL", "error");
            return;
        }

        showAlert(`Recibidos ${response.length} albaranes. Guardando...`, "info");

        // 2. Guardamos UNO A UNO (El puente necesario)
        for (const alb of response) {
             try {
                await q_guardar_albaran_api.run({
                    id_stel: alb.id,
                    referencia: alb['full-reference'] || alb.reference, 
                    fecha: alb.date, 
                    cliente: alb['customer-name'] || "Desconocido",
                    titulo: alb.title || "", 
                    importe_total: alb['total-amount'] || 0,
                    estado: alb['document-state-id']
                });
            } catch (error) {
                console.log("Error guardando albarán " + alb.id);
            }
        }

        // 3. Avisamos y refrescamos la tabla
        showAlert("¡Base de datos actualizada!", "success");
        if (typeof q_lista_albaranes !== 'undefined') q_lista_albaranes.run();
        if (typeof q_ficha_cabecera !== 'undefined') q_ficha_cabecera.run(); 
    }
}