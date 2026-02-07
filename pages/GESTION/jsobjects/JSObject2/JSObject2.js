export default {
  // helper
  n(x){ return Number(x || 0); },

  invoices() {
    return appsmith.store.invoices2025 || [];
  },

  kpis() {
    const inv = this.invoices();

    const total = inv.reduce((s,i)=> s + this.n(i["total-amount"]), 0);
    const paid  = inv.reduce((s,i)=> s + this.n(i["paid-total-amount"]), 0);
    const remaining = inv.reduce((s,i)=> s + this.n(i["remaining-total-amount"]), 0);

    const settledCount = inv.filter(i => i.settled === true).length;
    const pendingCount = inv.length - settledCount;

    return {
      count: inv.length,
      total,
      paid,
      remaining,
      settledCount,
      pendingCount
    };
  },

  eur(x){
    return new Intl.NumberFormat("es-ES", { style:"currency", currency:"EUR" }).format(this.n(x));
  }
}