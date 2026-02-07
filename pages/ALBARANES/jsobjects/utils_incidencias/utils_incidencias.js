export default {
  async sincronizarIncidencias() {
    // 1. Obtenemos las últimas 100 incidencias de la API de STEL
    const incidencias = await q_get_incidencias_api.run();
    
    // 2. Las guardamos una a una en nuestra base de datos
    for (let inc of incidencias) {
      await q_save_incidencias_db.run({
        id_stel: inc.id.toString(),         // Ejemplo: 5280523
        referencia: inc["full-reference"],  // Ejemplo: INC02574
        titulo: inc.description,            // Descripción del aviso
        fecha: inc.date.split('T')[0]       // Fecha limpia YYYY-MM-DD
      });
    }
    
    // 3. Recargamos la tabla de albaranes para ver los resultados
    await q_albaranes.run();
    
    showAlert("Incidencias traducidas correctamente", "success");
  }
}