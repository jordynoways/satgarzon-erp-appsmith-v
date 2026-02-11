export default {
    loading: false,

    analizarPedido: async () => {
        if (!FilePedido.files || FilePedido.files.length === 0) {
            showAlert("Sube un PDF o imagen primero", "warning");
            return;
        }
        try {
            const result = await API_Analizar_Pedido.run();
            const data = result;
            if (!data || !data.cesta) {
                showAlert("Error: no se recibieron datos del análisis", "error");
                return;
            }
            const cestaConStatus = data.cesta.map(item => ({
                ...item,
                status: item.precio > 0 ? "✅" : "❌"
            }));
            await storeValue("cesta", cestaConStatus);
            await storeValue("tipo_documento", data.tipo_documento || "ISTOBAL");
            await storeValue("titulo_lugar", data.titulo_lugar || "");
            await storeValue("pedido_ref", data.pedido_ref || "");
            await storeValue("direccion_envio", data.direccion_envio || "");
            showAlert("✅ " + cestaConStatus.length + " productos analizados (" + data.tipo_documento + ")", "success");
        } catch (error) {
            showAlert("❌ Error analizando: " + error.message, "error");
        }
    },

    confirmarPedido: async () => {
        const cesta = appsmith.store.cesta;
        if (!cesta || cesta.length === 0) {
            showAlert("No hay productos en la cesta", "warning");
            return;
        }
        try {
            const result = await API_Confirmar_Pedido.run();
            if (result && result.success) {
                showAlert("🚀 Pedido enviado a STEL Order", "success");
            } else {
                showAlert("⚠️ " + (result.message || "Error desconocido"), "error");
            }
        } catch (error) {
            showAlert("❌ Error confirmando: " + error.message, "error");
        }
    },

    calcularTotal: () => {
        const cesta = appsmith.store.cesta || [];
        return cesta.reduce((sum, item) => sum + (item.qty * item.precio), 0).toFixed(2);
    },

    limpiarTodo: async () => {
        await storeValue("cesta", []);
        await storeValue("tipo_documento", "");
        await storeValue("titulo_lugar", "");
        await storeValue("pedido_ref", "");
        await storeValue("direccion_envio", "");
        showAlert("🧹 Datos limpiados", "info");
    }
}
