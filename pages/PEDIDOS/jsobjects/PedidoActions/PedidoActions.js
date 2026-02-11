export default {
    loading: false,

    /**
     * Analiza un PDF/imagen subido usando Gemini Vision via FastAPI.
     * Resultado: cesta de productos validados contra tarifa.
     */
    analizarPedido: async () => {
        if (!FilePedido.files || FilePedido.files.length === 0) {
            showAlert("Sube un PDF o imagen primero", "warning");
            return;
        }

        this.loading = true;

        try {
            // Llamar al endpoint FastAPI
            const result = await API_Analizar_Pedido.run();
            const data = result;

            if (!data || !data.cesta) {
                showAlert("Error: no se recibieron datos del análisis", "error");
                return;
            }

            // Añadir status visual a cada línea
            const cestaConStatus = data.cesta.map(item => ({
                ...item,
                status: item.precio > 0 ? "✅" : "❌"
            }));

            // Guardar en store
            await storeValue("cesta", cestaConStatus);
            await storeValue("tipo_documento", data.tipo_documento || "ISTOBAL");
            await storeValue("titulo_lugar", data.titulo_lugar || "");
            await storeValue("pedido_ref", data.pedido_ref || "");
            await storeValue("direccion_envio", data.direccion_envio || "");
            await storeValue("direcciones_candidatas", data.direcciones_candidatas || []);

            showAlert(
                "✅ " + cestaConStatus.length + " productos analizados (" + data.tipo_documento + ")",
                "success"
            );

        } catch (error) {
            showAlert("❌ Error analizando: " + error.message, "error");
        } finally {
            this.loading = false;
        }
    },

    /**
     * Confirma y envía el pedido a STEL Order via FastAPI.
     */
    confirmarPedido: async () => {
        const cesta = appsmith.store.cesta;
        if (!cesta || cesta.length === 0) {
            showAlert("No hay productos en la cesta", "warning");
            return;
        }

        this.loading = true;

        try {
            const result = await API_Confirmar_Pedido.run();

            if (result && result.success) {
                showAlert("🚀 Pedido enviado a STEL Order correctamente", "success");
            } else {
                showAlert("⚠️ " + (result.message || "Error desconocido"), "error");
            }
        } catch (error) {
            showAlert("❌ Error confirmando: " + error.message, "error");
        } finally {
            this.loading = false;
        }
    },

    /**
     * Calcula el total de la cesta actual.
     */
    calcularTotal: () => {
        const cesta = appsmith.store.cesta || [];
        return cesta.reduce((sum, item) => sum + (item.qty * item.precio), 0).toFixed(2);
    },

    /**
     * Limpia la cesta y los datos del análisis.
     */
    limpiarTodo: async () => {
        await storeValue("cesta", []);
        await storeValue("tipo_documento", "");
        await storeValue("titulo_lugar", "");
        await storeValue("pedido_ref", "");
        await storeValue("direccion_envio", "");
        await storeValue("direcciones_candidatas", []);
        showAlert("🧹 Datos limpiados", "info");
    }
}
