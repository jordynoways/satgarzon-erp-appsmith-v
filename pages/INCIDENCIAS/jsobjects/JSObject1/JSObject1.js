export default {
    getClientName: (id) => {
        if (!get_clientes.data) return "Cargando...";
        // Buscamos convirtiendo todo a texto para que no falle
        const cliente = get_clientes.data.find(c => String(c.id) === String(id));
        return cliente ? cliente['legal-name'] : id; // Si no lo encuentra, devuelve el ID
    }
}