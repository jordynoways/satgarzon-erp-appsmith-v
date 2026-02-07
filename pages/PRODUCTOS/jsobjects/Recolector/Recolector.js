export default {
	async descargarTramoManual() {
		// Definimos el tramo
		const inicio = 100; 
		const cantidad = 100;

		try {
			// Llamada a la API
			const res = await q_getimagenes.run({ 
				"start": inicio, 
				"count": cantidad 
			});
			
			let datos = res.response || res;

			if (datos && datos.length > 0) {
				// Creamos la lista para el NAS
				const mapeo = datos.map(f => ({
					"antiguo": f["item-id"] + ".jpg",
					"nuevo": f.id + ".jpg"
				}));

				// ESTA LÍNEA dispara la descarga en tu navegador
				return download(mapeo, `mapeo_${inicio}_al_${inicio + cantidad}.json`, "text/plain");
			} else {
				showAlert("No hay datos en este tramo", "warning");
			}
		} catch (error) {
			showAlert("STEL te tiene bloqueado. Espera 10 min.", "error");
		}
	}
}