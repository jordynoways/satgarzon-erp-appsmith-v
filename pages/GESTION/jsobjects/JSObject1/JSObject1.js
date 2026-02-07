export default {
  // Ajustes
  PAGE_SIZE: 100,
  FROM_DATE: "2025-01-01T00:00:00.000Z",
  SLEEP_MS: 350, // freno anti "STEL se enfada"

  sleep(ms) {
    return new Promise((res) => setTimeout(res, ms));
  },

  toTime(d) {
    const t = new Date(d).getTime();
    return isNaN(t) ? 0 : t;
  },

  async fetchPage(start) {
    const limit = this.PAGE_SIZE;

    // Llamada al query (IMPORTANTE: pasar params)
    const res = await qInvoicesPage.run({ start, limit });

    // A veces AppSmith te devuelve objeto/array; normalizamos
    const arr = Array.isArray(res) ? res : (res?.data ?? res ?? []);

    return Array.isArray(arr) ? arr : [];
  },

  // Busca un rango donde ya aparezcan fechas 2025 sin barrer todo
  async findStartFor2025() {
    const target = this.toTime(this.FROM_DATE);

    // 1) probamos start=0
    let start = 0;
    let page = await this.fetchPage(start);
    await this.sleep(this.SLEEP_MS);

    if (!page.length) return 0;

    // Si ya hay algo 2025 en la primera página, no complicamos
    if (page.some(inv => this.toTime(inv.date) >= target)) return 0;

    // 2) saltos exponenciales hasta pasarnos (o hasta que se acabe)
    let lo = 0;
    let hi = 100;

    while (true) {
      const p = await this.fetchPage(hi);
      await this.sleep(this.SLEEP_MS);

      if (!p.length) {
        // no hay más páginas; devolvemos lo último que teníamos
        return lo;
      }

      const has2025 = p.some(inv => this.toTime(inv.date) >= target);
      if (has2025) break;

      lo = hi;
      hi = hi * 2;

      // tope de seguridad (evita loops infinitos)
      if (hi > 500000) return lo;
    }

    // 3) búsqueda binaria entre lo..hi
    while ((hi - lo) > this.PAGE_SIZE) {
      const mid = Math.floor((lo + hi) / 2 / this.PAGE_SIZE) * this.PAGE_SIZE;

      const p = await this.fetchPage(mid);
      await this.sleep(this.SLEEP_MS);

      if (!p.length) {
        hi = mid; // por si mid se pasa del final
        continue;
      }

      const has2025 = p.some(inv => this.toTime(inv.date) >= target);
      if (has2025) hi = mid;
      else lo = mid;
    }

    return Math.max(0, lo);
  },

  async fetchInvoicesFrom2025() {
    const target = this.toTime(this.FROM_DATE);

    // Encuentra el punto de arranque "cerca" de 2025
    const startNear = await this.findStartFor2025();

    // Ahora iteramos desde ahí y cogemos todo lo 2025+
    let start = Math.max(0, startNear);
    let all = [];
    let safety = 0;

    while (true) {
      const page = await this.fetchPage(start);
      await this.sleep(this.SLEEP_MS);

      if (!page.length) break;

      // Guardamos solo 2025+
      const filtered = page.filter(inv => this.toTime(inv.date) >= target);
      all.push(...filtered);

      // Si la página entera ya es 2025+ seguimos, si no… seguimos igualmente
      // pero ojo: si estamos muy cerca del cambio de año, habrá mezcla en 2024/2025.

      start += this.PAGE_SIZE;
      safety += 1;

      // tope seguridad (por si STEL se pone a mandar siempre lo mismo)
      if (safety > 2000) break;
    }

    // Guardamos para usar en tablas/KPIs
    storeValue("invoices2025", all, true);
    storeValue("invoices2025_count", all.length, true);

    return all;
  }
};