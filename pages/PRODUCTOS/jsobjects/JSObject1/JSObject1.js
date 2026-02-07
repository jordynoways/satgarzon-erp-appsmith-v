export default {
	modoEdicion: false, // Empezamos apagados

	// Función para encender
	activarEdicion: () => {
		this.modoEdicion = true;
	},

	// Función para apagar
	desactivarEdicion: () => {
		this.modoEdicion = false;
	}
}