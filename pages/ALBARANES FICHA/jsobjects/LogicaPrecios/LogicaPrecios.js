export default {
	// 1. TARIFAS (solo se usan si el usuario las solicita manualmente)
	tarifas: {
		istobal: { hora: 32.74, viaje: 35.08 },
		washtec: { hora: 39.00, viaje: 53.00, viaje_campsa: 50.00, hora_festiva: 54.00 },
		generico: { hora: 50.00, viaje: 65.00 },
		mides: { hora: 26.00 }
	},

	// HELPER: Obtener tarifa según el cliente seleccionado
	getTarifaCliente: function () {
		try {
			// Si no hay cliente seleccionado, devolvemos genérico (o null si prefieres no poner nada)
			if (!Select_public_clientes2 || !Select_public_clientes2.selectedOptionLabel) return this.tarifas.generico;

			const nombre = Select_public_clientes2.selectedOptionLabel.toUpperCase();

			if (nombre.includes("ISTOBAL")) return this.tarifas.istobal;
			if (nombre.includes("WASHTEC")) return this.tarifas.washtec;
			if (nombre.includes("MIDES")) return this.tarifas.mides;

			return this.tarifas.generico;
		} catch (e) {
			return this.tarifas.generico;
		}
	},

	// HELPER: Leer datos de forma segura
	getDatos: function () {
		return {
			lineas: (q_ficha_lineas && Array.isArray(q_ficha_lineas.data)) ? q_ficha_lineas.data : [],
			cabecera: (q_ficha_cabecera && Array.isArray(q_ficha_cabecera.data) && q_ficha_cabecera.data.length > 0) ? q_ficha_cabecera.data[0] : null
		};
	},

	// 1.5. ACTUALIZAR PRECIOS (Al cambiar cliente)
	actualizarPrecios: async function () {
		// Al cambiar el cliente, reseteamos los widgets para que lean el nuevo valor por defecto (calculado en las funciones obtener...)
		await resetWidget("InputPrecioBaseHt");
		await resetWidget("InputPreciobaseDs");
		await resetWidget("InputUnidadesHt");
		await resetWidget("InputUnidadesDs");
		await resetWidget("InputDescHt");
		await resetWidget("InputDescuentoDs");
	},


	// 2. PRECIO VIAJE - Solo devuelve si existe la línea en el albarán
	obtenerPrecioViaje: function () {
		const { lineas } = this.getDatos();

		const linea = lineas.find(l => {
			const ref = (l.referencia_articulo || "").toString().toUpperCase();
			const nom = (l.nombre_articulo || "").toUpperCase();
			return ref.startsWith('DS') || ref === 'SER00034' || ref === 'SER00037' || nom.includes('DESPLAZAMIENTO');
		});

		// Si existe la línea, devolver su precio. 
		if (linea && linea.precio_unitario !== undefined) {
			return parseFloat(linea.precio_unitario).toString();
		}

		// FALLBACK: Si es un albarán nuevo (sin líneas) y tenemos cliente seleccionado
		const tarifa = this.getTarifaCliente();
		if (tarifa && tarifa.viaje) return tarifa.viaje.toString();

		return ""; // No hay línea y no hay tarifa aplicable
	},

	// 3. UNIDADES VIAJE - Solo devuelve si existe la línea
	obtenerUnidadesViaje: function () {
		const { lineas } = this.getDatos();
		const linea = lineas.find(l => {
			const ref = (l.referencia_articulo || "").toString().toUpperCase();
			const nom = (l.nombre_articulo || "").toUpperCase();
			return ref.startsWith('DS') || ref === 'SER00034' || ref === 'SER00037' || nom.includes('DESPLAZAMIENTO');
		});

		// Si existe la línea, devolver su cantidad.
		if (linea && linea.cantidad !== undefined) {
			return parseFloat(linea.cantidad).toString();
		}

		// FALLBACK: Default 1 si hay cliente seleccionado
		if (Select_public_clientes2.selectedOptionLabel) return "1";

		return "";
	},

	// 4. PRECIO HORA - Solo devuelve si existe la línea en el albarán
	obtenerPrecioHora: function () {
		const { lineas } = this.getDatos();
		const linea = lineas.find(l => {
			const ref = (l.referencia_articulo || "").toString().toUpperCase();
			const nom = (l.nombre_articulo || "").toUpperCase();
			return (ref.startsWith('HT') || ref === 'SER00031') && !nom.includes('VIAJE');
		});

		// Si existe la línea, devolver su precio.
		if (linea && linea.precio_unitario !== undefined) {
			return parseFloat(linea.precio_unitario).toString();
		}

		// FALLBACK: Tarifa cliente
		const tarifa = this.getTarifaCliente();
		if (tarifa && tarifa.hora) return tarifa.hora.toString();

		return "";
	},

	// 5. UNIDADES HORA - Solo devuelve si existe la línea
	obtenerUnidadesHora: function () {
		const { lineas } = this.getDatos();
		const linea = lineas.find(l => {
			const ref = (l.referencia_articulo || "").toString().toUpperCase();
			const nom = (l.nombre_articulo || "").toUpperCase();
			return (ref.startsWith('HT') || ref === 'SER00031') && !nom.includes('VIAJE');
		});

		// Si existe la línea, devolver su cantidad.
		if (linea && linea.cantidad !== undefined) {
			return parseFloat(linea.cantidad).toString();
		}

		// FALLBACK: Default 1 si hay cliente seleccionado
		if (Select_public_clientes2.selectedOptionLabel) return "1";

		return "";
	},

	// 5.5. DESCUENTO HORA - Solo devuelve si existe la línea
	obtenerDescuentoHora: function () {
		const { lineas } = this.getDatos();
		const linea = lineas.find(l => {
			const ref = (l.referencia_articulo || "").toString().toUpperCase();
			const nom = (l.nombre_articulo || "").toUpperCase();
			return (ref.startsWith('HT') || ref === 'SER00031') && !nom.includes('VIAJE');
		});

		if (linea && linea.descuento_porcentaje !== undefined) {
			return parseFloat(linea.descuento_porcentaje).toString();
		}

		// FALLBACK: 0
		if (Select_public_clientes2.selectedOptionLabel) return "0";

		return "";
	},

	// 5.6. DESCUENTO VIAJE - Solo devuelve si existe la línea
	obtenerDescuentoViaje: function () {
		const { lineas } = this.getDatos();
		const linea = lineas.find(l => {
			const ref = (l.referencia_articulo || "").toString().toUpperCase();
			const nom = (l.nombre_articulo || "").toUpperCase();
			return ref.startsWith('DS') || ref === 'SER00034' || ref === 'SER00037' || nom.includes('DESPLAZAMIENTO');
		});

		if (linea && linea.descuento_porcentaje !== undefined) {
			return parseFloat(linea.descuento_porcentaje).toString();
		}

		// FALLBACK: 0
		if (Select_public_clientes2.selectedOptionLabel) return "0";

		return "";
	},

	// 6. DATOS TABLA (Corregido para evitar duplicados)
	getMaterialesTabla: function () {
		const dataLineas = (q_ficha_lineas && Array.isArray(q_ficha_lineas.data)) ? q_ficha_lineas.data : [];
		const localLines = appsmith.store.localLines || [];

		const allLines = [...dataLineas, ...localLines];

		if (!allLines || allLines.length === 0) return [];

		return allLines
			.filter(l => {
				const ref = (l.referencia_articulo || "").toString().trim().toUpperCase();
				const nom = (l.nombre_articulo || "").toString().trim().toUpperCase();

				if (!nom || nom === "" || nom === "PO" || nom.includes("TRABAJOS REALIZADOS") || nom.includes("MATERIALES UTILIZADOS") || nom.includes("MATERIAL UTILIZADO") || nom === "MATERIALES" || (nom.includes("MATERIALES") && parseFloat(l.precio_unitario || 0) === 0) || ref === 'SER00035') return false;
				if (ref === 'SER00037' || ref === 'SER00034' || ref.startsWith('DS') || nom.includes("DESPLAZAMIENTO") || nom.includes("PORTES")) return false;
				if (ref.startsWith('HT') || ref === 'SER00031') return false;

				return true;
			})
			.map(l => {
				const precio = parseFloat(l.precio_unitario || 0);
				const cantidad = parseFloat(l.cantidad || 0);
				const descuento = parseFloat(l.descuento_porcentaje || 0);
				const subtotalNum = (precio * cantidad) * (1 - (descuento / 100));

				return {
					id: l.id || l.id_stel,
					Referencia: l.referencia_articulo || "",
					Descripcion: l.nombre_articulo || "",
					Cantidad: cantidad,
					Precio: precio,
					Descuento: descuento,
					Subtotal: subtotalNum.toFixed(2) + " €"
				};
			});
	},

	// 7. CÁLCULOS TOTALES DESGLOSADOS
	calcularTotales: function () {
		// A. Servicios (Horas + Desplazamiento) - Acceso directo a widgets
		const horasQty = parseFloat(InputUnidadesHt?.text || "0") || 0;
		const horasPrc = parseFloat((InputPrecioBaseHt?.text || "0").toString().replace("€", "").replace(",", ".")) || 0;
		const horasDto = parseFloat((InputDescHt?.text || "0").toString().replace("%", "").replace(",", ".")) || 0;
		const totalHoras = (horasQty * horasPrc) * (1 - (horasDto / 100));

		const despQty = parseFloat(InputUnidadesDs?.text || "0") || 0;
		const despPrc = parseFloat((InputPreciobaseDs?.text || "0").toString().replace("€", "").replace(",", ".")) || 0;
		const despDto = parseFloat((InputDescuentoDs?.text || "0").toString().replace("%", "").replace(",", ".")) || 0;
		const totalDesp = (despQty * despPrc) * (1 - (despDto / 100));

		const subtotalServicios = totalHoras + totalDesp;

		// B. Materiales (Sumatorio de la tabla: DB + Local + Filtrado robusto)
		const dataLineas = (q_ficha_lineas && Array.isArray(q_ficha_lineas.data)) ? q_ficha_lineas.data : [];
		const localLines = appsmith.store.localLines || [];
		const allLines = [...dataLineas, ...localLines];

		const subtotalMateriales = allLines
			.filter(l => {
				const ref = (l.referencia_articulo || "").toString().trim().toUpperCase();
				const nom = (l.nombre_articulo || "").toString().trim().toUpperCase();

				if (!nom || nom === "" || nom === "PO" || nom.includes("TRABAJOS REALIZADOS") || nom.includes("MATERIALES UTILIZADOS") || nom.includes("MATERIAL UTILIZADO") || nom === "MATERIALES" || (nom.includes("MATERIALES") && parseFloat(l.precio_unitario || 0) === 0) || ref === 'SER00035') return false;
				if (ref === 'SER00037' || ref === 'SER00034' || ref.startsWith('DS') || nom.includes("DESPLAZAMIENTO") || nom.includes("PORTES")) return false;
				if (ref.startsWith('HT') || ref === 'SER00031') return false;

				return true;
			})
			.reduce((acc, linea) => {
				const precio = parseFloat(linea.precio_unitario || 0);
				const cantidad = parseFloat(linea.cantidad || 0);
				const descuento = parseFloat(linea.descuento_porcentaje || 0);
				return acc + ((precio * cantidad) * (1 - (descuento / 100)));
			}, 0);

		// C. Totales Finales
		const baseImponible = subtotalServicios + subtotalMateriales;
		const iva = baseImponible * 0.21;
		const total = baseImponible + iva;

		return {
			servicios: subtotalServicios.toFixed(2),
			materiales: subtotalMateriales.toFixed(2),
			base: baseImponible.toFixed(2),
			iva: iva.toFixed(2),
			total: total.toFixed(2)
		};
	},

	// 8. CRUD UNIFICADO (DB + LOCAL)
	// ------------------------------------------------------------------------------------

	// GUARDAR (EDICIÓN)
	guardarLinea: async function (newRow) {
		showAlert("Iniciando guardado...", "info");
		console.log("guardarLinea called with:", newRow);
		if (!newRow) {
			showAlert("Error: newRow es nulo/indefinido", "error");
			return;
		}

		if (!newRow.id) {
			showAlert("Error: No se pudo identificar la fila (Falta ID).", "error");
			return;
		}


		// Limpiar precio (ya viene limpio si es number, pero por seguridad quitamos símbolos si es string)
		const precioClean = (typeof newRow.Precio === 'number')
			? newRow.Precio
			: parseFloat((newRow.Precio || '0').toString().replace(' €', '').replace('€', '').trim());

		// Identificar si es línea local
		const idStr = newRow.id ? newRow.id.toString() : "";
		const isLocal = idStr.startsWith('loc_');
		const noHayAlbaran = !appsmith.URL.queryParams.id;

		if (isLocal || noHayAlbaran) {
			// --- ACTUALIZACIÓN LOCAL ---
			let lines = appsmith.store.localLines || [];
			const idx = lines.findIndex(l => l.id == newRow.id); // Loose equality just in case

			const lineObj = {
				id: newRow.id || 'loc_' + Date.now(),
				referencia_articulo: newRow.Referencia,
				nombre_articulo: newRow.Descripcion,
				cantidad: newRow.Cantidad,
				precio_unitario: precioClean,
				descuento_porcentaje: newRow.Descuento,
				importe_total: (parseFloat(newRow.Cantidad) * parseFloat(precioClean) * (1 - (parseFloat(newRow.Descuento) / 100)))
			};

			if (idx >= 0) {
				lines[idx] = { ...lines[idx], ...lineObj };
			} else {
				// Si no existe (raro en guardar), lo añadimos
				lines.push(lineObj);
			}

			await storeValue('localLines', lines);
			showAlert('Fila actualizada (Local)', 'success');
		} else {
			// --- ACTUALIZACIÓN DB ---
			try {
				await q_update_linea_albaran.run({
					id: parseInt(newRow.id),
					referencia: newRow.Referencia,
					descripcion: newRow.Descripcion,
					cantidad: parseFloat(newRow.Cantidad || 0),
					precio: precioClean,
					descuento: parseFloat(newRow.Descuento || 0)
				});
				await q_ficha_lineas.run();
				showAlert('Fila actualizada', 'success');
			} catch (err) {
				showAlert('Error al actualizar fila: ' + err.message, 'error');
			}
		}
	},

	// CREAR (NUEVA FILA)
	crearLinea: async function (newRow) {
		const precioClean = (typeof newRow.Precio === 'number')
			? newRow.Precio
			: parseFloat((newRow.Precio || '0').toString().replace(' €', '').replace('€', '').trim());
		const noHayAlbaran = !appsmith.URL.queryParams.id;

		if (noHayAlbaran) {
			// --- CREACIÓN LOCAL ---
			const lineObj = {
				id: 'loc_' + Date.now(),
				referencia_articulo: newRow.Referencia,
				nombre_articulo: newRow.Descripcion,
				cantidad: newRow.Cantidad || 1,
				precio_unitario: precioClean,
				descuento_porcentaje: newRow.Descuento || 0,
				importe_total: (parseFloat(newRow.Cantidad || 1) * parseFloat(precioClean || 0) * (1 - (parseFloat(newRow.Descuento || 0) / 100)))
			};

			let lines = appsmith.store.localLines || [];
			lines.push(lineObj);
			await storeValue('localLines', lines);
			showAlert('Fila añadida (Local)', 'success');
		} else {
			// --- CREACIÓN DB ---
			try {
				await q_insert_linea_albaran.run({
					referencia: newRow.Referencia,
					descripcion: newRow.Descripcion,
					cantidad: newRow.Cantidad,
					precio: precioClean,
					descuento: newRow.Descuento
				});
				await q_ficha_lineas.run();
				showAlert('Fila añadida con éxito', 'success');
			} catch (err) {
				showAlert('Error al añadir fila: ' + err.message, 'error');
			}
		}
	},

	// BORRAR
	borrarLinea: async function (row) {
		const idStr = row.id ? row.id.toString() : "";
		const isLocal = idStr.startsWith('loc_');

		if (isLocal) {
			let lines = appsmith.store.localLines || [];
			lines = lines.filter(l => l.id != row.id);
			await storeValue('localLines', lines);
			showAlert('Línea eliminada (Local)', 'success');
		} else {
			try {
				await q_delete_linea_albaran.run({ id: row.id });
				await q_ficha_lineas.run();
				showAlert('Línea eliminada', 'success');
			} catch (err) {
				showAlert('Error al eliminar fila: ' + err.message, 'error');
			}
		}
	}
}