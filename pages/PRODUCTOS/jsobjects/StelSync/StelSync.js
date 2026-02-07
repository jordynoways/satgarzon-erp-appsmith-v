export default {
    async syncIds() {
        let start = 0;
        let hasMore = true;
        let updatedCount = 0;
        let errorCount = 0;

        try {
            while (hasMore) {
                // Fetch products from STEL Order
                const response = await Stel_GetProducts.run({ start: start });

                if (!response || response.length === 0) {
                    hasMore = false;
                    break;
                }

                // Bulk Upsert items
                try {
                    await q_upsertProductsStel.run({ products: response });
                    updatedCount += response.length;
                } catch (bulkError) {
                    console.error("Bulk sync failed, attempting individual sync...", bulkError);
                    // Fallback: process item by item to isolate errors
                    for (const product of response) {
                        try {
                            await q_upsertProductsStel.run({ products: [product] });
                            updatedCount++;
                        } catch (singleError) {
                            console.error(`Failed to sync product ${product.reference} (${product.id}):`, singleError);
                            errorCount++;
                        }
                    }
                }


                // STOP after first batch (fetch only last 100 products)
                hasMore = false;
            }

            try {
                await API_ListarProductos.run();
            } catch (refreshErr) {
                console.warn("Failed to refresh table:", refreshErr);
            }
            showAlert(`Synchronized ${updatedCount} products from Stel Order. Failed: ${errorCount}`, 'success');

        } catch (error) {
            console.error("Sync failed:", error);
            showAlert(`Sync failed: ${error.message}`, 'error');
        }
    }
}
