export default {
    async sincronizarFacturasMasivo() {
        // COMENTAMOS EL TRUNCATE para no perder lo que ya hemos bajado hoy
        // await q_truncar_facturas.run(); 
        
        // CAMBIA ESTE NÚMERO: Pon aquí el último número que viste en el log
        // Si se quedó en "Página completada: 1500", pon 1500 aquí:
        let registroInicial = 0; 
        
        let tamanoBloque = 100; 
        let continuar = true;

        try {
            while (continuar) {
                const data = await get_facturas_stel.run({ 
                    start: registroInicial, 
                    limit: tamanoBloque 
                });

                if (!data || !Array.isArray(data) || data.length === 0) {
                    continuar = false;
                    break;
                }

                await q_importar_facturas.run({
                    json_data: JSON.stringify(data)
                });

                console.log("Sincronizado hasta el registro: " + registroInicial);
                registroInicial += tamanoBloque; 
                
                await new Promise(r => setTimeout(r, 1000)); // Pausa más larga (1 seg) para ser más "amables" con la API
            }
            showAlert("Sincronización completada con éxito", "success");
        } catch (e) {
            showAlert("Límite de API alcanzado. Continuaremos mañana desde el registro " + registroInicial, "warning");
        }
    }
}