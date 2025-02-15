import { ClockManager } from './ClockManager.js';

export function initializeClocks() {
    console.log('Initializing clocks...');
    window.clockManager = new ClockManager();
}
