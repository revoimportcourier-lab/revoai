// Configuración del flujo C (revisar trabajos en curso, QA con GPT-6 Astra y formatos 1:1 / 9:16).
// Si tu cuenta de OpenAI aún no tiene acceso a gpt-6-astra, pon aquí otro modelo de OpenAI con visión que sí tengas.
return [{
  json: {
    sheet_url: 'PEGA_AQUI_EL_LINK_DE_TU_GOOGLE_SHEET',
    openai_model: 'gpt-6-astra',
    resolucion: '2k',
    calidad: 'high',
  },
}];
