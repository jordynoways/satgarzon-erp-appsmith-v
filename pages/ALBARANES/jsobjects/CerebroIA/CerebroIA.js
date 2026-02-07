export default {
	filtros: { 
		inicio: moment().startOf('month').format("YYYY-MM-DD"), 
		fin: moment().format("YYYY-MM-DD"), 
		busqueda: "" 
	},
	respuestaTexto: "",

	async interpretarPregunta() {
		const pregunta = (Input_Pregunta.text || "").trim();
		if (!pregunta) return;
		await API_Gemini.run({
			instruccion: "Hoy es " + moment().format("DD/MM/YYYY") + ". Analiza la petición: '" + pregunta + "'. Extrae fechas y responde SOLO JSON: {\"inicio\":\"YYYY-MM-DD\", \"fin\":\"YYYY-MM-DD\", \"busqueda\": \"\"}"
		});
		try {
			const resText = API_Gemini.data.candidates[0].content.parts[0].text;
			const jsonMatch = resText.match(/\{[\s\S]*\}/);
			if (jsonMatch) {
				const res = JSON.parse(jsonMatch[0]);
				this.filtros.inicio = res.inicio;
				this.filtros.fin = res.fin;
			}
		} catch (e) { console.log("Error fechas", e); }
	},

	async ejecutarConsulta() {
		this.respuestaTexto = "🛸 ANTIGRAVITY analizando beneficios y desglosando recambios...";
		
		// 1. Entender qué fechas quieres (desde 2017 a hoy)
		await this.interpretarPregunta();
		
		// 2. Ejecutar las DOS consultas en paralelo para ir más rápido
		const [resRentabilidad, resPiezas] = await Promise.all([
			Query_Rentabilidad_Antigravity.run(),
			Query_Top_Piezas.run()
		]);
		
		if (!resRentabilidad || resRentabilidad.length === 0) {
			this.respuestaTexto = "❌ No hay registros para el periodo solicitado.";
			return;
		}

		// 3. Informe Global con Gemini
		await API_Gemini.run({
			instruccion: `Eres ANTIGRAVITY, Auditor de Garzón. 
			
			OBJETIVO:
			1. Informe Rentabilidad: (Venta, Gastos y Beneficio Neto usando 14€/h y 16,50€ viaje).
			2. Análisis de Piezas: Identifica qué materiales se han puesto más usando el listado adjunto.
			
			IMPORTANTE: Si el jefe pregunta por piezas de enero, usa el listado de 'DETALLE PIEZAS' para darle nombres y cantidades exactas. No digas que no tienes los datos.`,
			promptChat: "DATOS GENERALES: " + JSON.stringify(resRentabilidad.slice(0, 35)) + 
			            " | DETALLE PIEZAS: " + JSON.stringify(resPiezas)
		});

		this.respuestaTexto = API_Gemini.data.candidates[0].content.parts[0].text;
	}
}