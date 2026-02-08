export default {
    importarDeStel: async () => {
        try {
            // 1. Llamar a la API de STEL
            const empleados = await get_empleados_stel.run();

            if (!empleados || empleados.length === 0) {
                showAlert('No se encontraron empleados en STEL', 'warning');
                return;
            }

            let insertados = 0;
            let errores = 0;

            // 2. Insertar cada empleado
            for (const emp of empleados) {
                const nombre = emp.name || emp['employee-name'] || emp.nombre || '';
                const apellidos = emp.surname || emp['employee-surname'] || emp.apellidos || '';
                const email = emp.email || '';
                const telefono = emp.phone || emp.telefono || '';

                if (!nombre) continue;

                try {
                    await Import_Empleado_Stel.run({
                        nombre: nombre,
                        apellidos: apellidos,
                        email: email,
                        telefono: telefono
                    });
                    insertados++;
                } catch (e) {
                    errores++;
                }
            }

            // 3. Refrescar tabla
            await Get_Empleados_DB.run();
            showAlert(`Importados: ${insertados} empleados. Errores: ${errores}`, 'success');

        } catch (error) {
            showAlert('Error al importar: ' + error.message, 'error');
        }
    }
}
