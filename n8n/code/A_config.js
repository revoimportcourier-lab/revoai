// Configuración del flujo A (actualizar biblioteca con Claude).
// Pega el link de tu Google Sheet (la que creaste importando prompts/banners.csv).
return [{
  json: {
    sheet_url: 'PEGA_AQUI_EL_LINK_DE_TU_GOOGLE_SHEET',
    claude_model: 'claude-opus-5-5',
    claude_effort: 'medium',
  },
}];
