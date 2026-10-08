// Lee window.OK_CONFIG de revoimport.com/config.js y arma la ficha de cada producto.
// La huella cambia cuando cambian nombre, precios, precio anterior, colores, contenido o fotos.
const SITE = 'https://revoimport.com';
const raw = $input.first().json.data;

function parseConfig(text) {
  const start = text.indexOf('window.OK_CONFIG');
  const open = text.indexOf('{', start);
  if (start < 0 || open < 0) throw new Error('No se encontró window.OK_CONFIG en config.js');
  let depth = 0;
  let quote = '';
  let esc = false;
  for (let i = open; i < text.length; i++) {
    const c = text[i];
    if (quote) {
      if (esc) esc = false;
      else if (c === '\\') esc = true;
      else if (c === quote) quote = '';
      continue;
    }
    if (c === '"' || c === "'") quote = c;
    else if (c === '{') depth++;
    else if (c === '}' && --depth === 0) return JSON.parse(text.slice(open, i + 1));
  }
  throw new Error('config.js incompleto');
}

const abs = (p) => (p ? (p.startsWith('http') ? p : `${SITE}/${p.replace(/^\//, '')}`) : null);
const soles = (n) => `S/ ${Number(n).toLocaleString('en-US')}`;
const hash = (s) => {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0;
  return h.toString(16).padStart(8, '0');
};
const uniq = (a) => [...new Set(a.filter((x) => x !== null && x !== undefined && x !== ''))];

const cfg = parseConfig(raw);
const promoIphone = (cfg.giftPromotions || []).find((g) => g.id === 'iphone-four');
const global = {
  marca: cfg.brand,
  whatsapp: `+${cfg.country} ${cfg.whatsapp}`,
  pagos: cfg.payments || [],
  envios: cfg.shipping || {},
  regalos_iphone: promoIphone && promoIphone.enabled ? promoIphone.gifts.map((g) => g.name) : [],
  nota_regalos: promoIphone ? promoIphone.note : '',
};

return (cfg.products || []).map((p) => {
  const variants = p.variants || [];
  const precios = uniq(variants.map((v) => v.price)).sort((a, b) => a - b);
  const imgs = [];
  for (const arr of Object.values(p.galleries || {})) imgs.push(...arr.slice(0, 3));
  for (const k of ['cover', 'image']) if (p[k]) imgs.push(p[k]);
  for (const g of p.galleryViews || []) if (g && g.src) imgs.push(g.src);
  const ficha = {
    id: p.id,
    nombre: p.name,
    categoria: p.category,
    precio: precios.length > 1 ? `Desde ${soles(precios[0])}` : precios.length ? soles(precios[0]) : '',
    precio_antes: p.previousPrice ? soles(p.previousPrice) : null,
    precios,
    capacidades: uniq(variants.map((v) => v.capacity)),
    sim: uniq(variants.map((v) => v.sim)),
    colores: (p.colors || []).map((c) => c.name),
    tamano: p.size || null,
    descripcion: p.description || '',
    incluye: p.includes || [],
    etiqueta: p.conditionBadge || p.sourceBadge || p.label || p.tag || null,
    garantia: p.warranty || null,
    original: p.genuine === undefined ? null : p.genuine,
    nota_autenticidad: p.authenticityNote || null,
    envio: p.deliveryOffer || null,
    disponibilidad: uniq(variants.map((v) => v.availability)),
    link: `${SITE}/p/${p.id}/`,
    imagenes: uniq(imgs.map(abs)),
    global,
  };
  ficha.huella = hash(JSON.stringify({
    n: ficha.nombre, p: ficha.precios, a: ficha.precio_antes, c: ficha.colores, i: ficha.incluye, im: ficha.imagenes,
  }));
  return { json: ficha };
});
