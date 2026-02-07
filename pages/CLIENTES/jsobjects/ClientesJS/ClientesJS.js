export default {
	async sincronizarClientesMasivo() {
		let registroInicial = 0; 
		let tamanoBloque = 100; // El 'limit' de tu documentación
		let continuar = true;

		try {
			while (continuar) {
				// 1. Llamada usando los nombres exactos de tu DOC: start y limit
				const data = await get_clientes_stel.run({ 
					start: registroInicial, 
					limit: tamanoBloque 
				});

				// 2. Si no hay datos o no es una lista, paramos
				if (!data || !Array.isArray(data) || data.length === 0) {
					console.log("Sincronización finalizada: No hay más registros.");
					continuar = false;
					break;
				}

				try {
					// 3. Importación masiva a PostgreSQL
					await q_importar_masivo.run({
						json_data: JSON.stringify(data)
					});
					console.log(`Sincronizados registros desde el ${registroInicial}`);
				} catch (dbErr) {
					console.error(`Error en bloque ${registroInicial}:`, dbErr.message);
				}

				// 4. Incrementamos el inicio según el límite (0, 100, 200...)
				registroInicial += tamanoBloque; 
				
				// Pausa de cortesía para la API
				await new Promise(r => setTimeout(r, 800));
			}

			showAlert("Sincronización masiva terminada con éxito", "success");
			await Select_public_clientes1.run();

		} catch (e) {
			showAlert("Error crítico: " + e.message, "error");
		}
	}
}