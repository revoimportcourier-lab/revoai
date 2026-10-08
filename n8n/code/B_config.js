// Configuración del flujo B (generar en Higgsfield las filas con estado "aprobado").
// max_por_corrida limita cuántos banners se envían por clic (cada uno = 1 master + 2 formatos).
return [{
  json: {
    sheet_url: 'PEGA_AQUI_EL_LINK_DE_TU_GOOGLE_SHEET',
    max_por_corrida: 2,
    resolucion: '2k',
    calidad: 'high',
  },
}];
