export default {
  agregarMaterial: () => {
    // 1. Recuperar la lista actual (o crear una nueva si está vacía)
    let lista = appsmith.store.cesta_materiales || [];

    // 2. Crear el nuevo objeto con lo seleccionado
    const nuevoItem = {
      id: SelectProducto.selectedOptionValue,
      nombre: SelectProducto.selectedOptionLabel,
      cantidad: Number(CantMaterial.text) || 1
    };

    // 3. Añadirlo a la lista y guardar
    if (nuevoItem.id) {
      lista.push(nuevoItem);
      storeValue('cesta_materiales', lista);

      // 4. Limpiar los campos para poner otro
      resetWidget("SelectProducto");
      resetWidget("CantMaterial");
    } else {
      showAlert("⚠️ Selecciona un producto primero", "warning");
    }
  }
}