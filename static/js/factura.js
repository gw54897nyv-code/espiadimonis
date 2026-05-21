document.addEventListener('DOMContentLoaded', function () {
  var productes = JSON.parse(document.getElementById('productes-data')?.textContent || '[]');
  var clients   = JSON.parse(document.getElementById('clients-data')?.textContent || '[]');

  // ── Autocomplete client ──────────────────────────────────────────────────
  var clientSelect = document.getElementById('id_client_registrat');
  if (clientSelect) {
    clientSelect.addEventListener('change', function () {
      var id = parseInt(this.value);
      var client = clients.find(function (c) { return c.id === id; });
      if (client) {
        var nomField    = document.querySelector('[name="client"]');
        var nifField    = document.querySelector('[name="nif_client"]');
        var adrecaField = document.querySelector('[name="adreca_client"]');
        if (nomField)    nomField.value    = client.nom    || '';
        if (nifField)    nifField.value    = client.nif    || '';
        if (adrecaField) adrecaField.value = client.adreca || '';
      }
    });
  }

  // ── Autocomplete producte en cada línia ──────────────────────────────────
  function bindProducteSelect(linia) {
    var sel = linia.querySelector('.producte-select');
    if (!sel) return;
    sel.addEventListener('change', function () {
      var id = parseInt(this.value);
      var prod = productes.find(function (p) { return p.id === id; });
      if (prod) {
        var desc = linia.querySelector('input[name$="-descripcio"]');
        var preu = linia.querySelector('input[name$="-preu_unitari"]');
        if (desc) desc.value = prod.descripcio || prod.nom;
        if (preu) preu.value = prod.preu_unitari.toFixed(2);
        calcular();
      }
    });
  }

  document.querySelectorAll('.linia-factura').forEach(bindProducteSelect);

  // ── Càlcul de totals ─────────────────────────────────────────────────────
  function calcular() {
    var subtotal = 0;
    document.querySelectorAll('.linia-factura').forEach(function (row) {
      var del = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (del && del.checked) { row.style.opacity = '0.4'; return; }
      row.style.opacity = '1';
      var qty  = parseFloat(row.querySelector('input[name$="-quantitat"]')?.value)    || 0;
      var preu = parseFloat(row.querySelector('input[name$="-preu_unitari"]')?.value) || 0;
      var imp  = qty * preu;
      var span = row.querySelector('.import-linia');
      if (span) span.textContent = imp.toFixed(2) + ' €';
      subtotal += imp;
    });

    var exemptCheck = document.querySelector('[name="exempt_iva"]');
    var exempt = exemptCheck && exemptCheck.checked;
    var ivaInput = document.querySelector('[name="iva"]');
    var iva = exempt ? 0 : (parseFloat(ivaInput?.value) || 21);
    var importIva = subtotal * iva / 100;
    var total = subtotal + importIva;

    var fmt = function (n) { return n.toFixed(2).replace('.', ',') + ' €'; };
    var subEl = document.getElementById('resum-subtotal');
    var ivaEl = document.getElementById('resum-iva');
    var totEl = document.getElementById('resum-total');
    if (subEl) subEl.textContent = fmt(subtotal);
    if (ivaEl) ivaEl.textContent = fmt(importIva);
    if (totEl) totEl.textContent = fmt(total);
  }

  document.addEventListener('input',  calcular);
  document.addEventListener('change', calcular);
  calcular();

  // ── Afegir línia ──────────────────────────────────────────────────────────
  var btn = document.getElementById('afegir-linia');
  if (btn) {
    btn.addEventListener('click', function () {
      var container  = document.getElementById('linies-container');
      var totalForms = document.querySelector('[name$="-TOTAL_FORMS"]');
      if (!container || !totalForms) return;

      var count  = parseInt(totalForms.value);
      var prefix = totalForms.name.replace('-TOTAL_FORMS', '');
      var re     = new RegExp('^(' + prefix + ')-(\\d+)-');

      var template = container.querySelector('.linia-factura');
      if (!template) return;
      var nova = template.cloneNode(true);

      nova.querySelectorAll('[name]').forEach(function (el) {
        el.name = el.name.replace(re, '$1-' + count + '-');
        if (el.type === 'checkbox') el.checked = false;
        else el.value = '';
        if (el.tagName === 'SELECT') el.selectedIndex = 0;
      });
      nova.querySelectorAll('[id]').forEach(function (el) {
        el.id = el.id.replace(
          new RegExp('^(id_' + prefix + ')-(\\d+)-'),
          '$1-' + count + '-'
        );
      });
      var importSpan = nova.querySelector('.import-linia');
      if (importSpan) importSpan.textContent = '—';
      nova.style.opacity = '1';

      container.appendChild(nova);
      totalForms.value = count + 1;
      bindProducteSelect(nova);
    });
  }
});
