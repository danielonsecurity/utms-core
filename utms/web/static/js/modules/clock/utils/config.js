export function validateConfig(config) {
    if (!config) {
        throw new Error('Clock configuration is required');
    }
    const requiredFields = ['name', 'hands', 'outerScale'];
    requiredFields.forEach(field => {
      if (!config[field]) {
        throw new Error(`Missing required field: ${field}`);
      }
    });
    
    if (!Array.isArray(config.hands) || config.hands.length === 0) {
      throw new Error('At least one hand configuration is required');
    }

}

export const defaultConfig = {
  // Default configuration values
};
