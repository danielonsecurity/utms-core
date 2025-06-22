import { Clock } from './Clock.js';
import { findFreePosition } from './utils/position.js';


export class ClockManager {
  constructor() {
    this.clocks = new Map();
    this.initializeUI();
  }

  initializeUI() {
    const addBtn = document.getElementById('addClockBtn');
    addBtn.addEventListener('click', () => this.showClockModal());
    this.initializeModal();
    this.loadSavedClocks();
  }

  showClockModal(existingConfig = null) {
    const modal = document.getElementById('clockConfigModal');
    const form = document.getElementById('clockConfigForm');
    
    form.reset();
    this.editingClockId = existingConfig?.id;

    if (existingConfig) {
      this.populateForm(form, existingConfig);
    }

    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent body scrolling

  }

  hideModal() {
    const modal = document.getElementById('clockConfigModal');
    modal.style.display = 'none';
    document.body.style.overflow = ''; // Restore body scrolling
  }

  addClock(config) {
    try {
      // Only find free position if position is not provided
      if (!config.position) {
        config.position = findFreePosition(this.clocks);
      }
      
      const clock = new Clock(config);
      const container = document.getElementById('clocksGrid');

      if (!container) {
        throw new Error('Clock grid container not found');
      }

      // Set initial position using transform
      clock.element.style.transform = `translate(${config.position.x}px, ${config.position.y}px)`;

      container.appendChild(clock.element);
      this.clocks.set(config.id, clock);
      this.saveClocks();
    } catch (error) {
      console.error('Failed to add clock:', error);
      alert('Failed to add clock: ' + error.message);
    }
  }

  updateClock(config) {
    this.deleteClock(config.id);
    this.addClock(config);
  }



  checkCollisionWithExisting(position, width, height) {
    const margin = 10;
    const newBounds = {
      left: position.x,
      right: position.x + width,
      top: position.y,
      bottom: position.y + height
    };

    for (const clock of this.clocks.values()) {
      const bounds = clock.element.getBoundingClientRect();
      
      if (!(newBounds.right + margin < bounds.left ||
            newBounds.left > bounds.right + margin ||
            newBounds.bottom + margin < bounds.top ||
            newBounds.top > bounds.bottom + margin)) {
        return true;
      }
    }
    return false;
  }

  deleteClock(id) {
    const clock = this.clocks.get(id);
    if (clock) {
      clock.destroy();
      this.clocks.delete(id);
      this.saveClocks();
    }
  }

  saveClocks() {
    const configs = Array.from(this.clocks.values()).map(clock => clock.config);
    try {
      localStorage.setItem('clockConfigs', JSON.stringify(configs));
    } catch (error) {
      console.error('Failed to save clocks:', error);
    }
  }

  loadSavedClocks() {
    try {
      const savedConfigs = localStorage.getItem('clockConfigs');
      if (savedConfigs) {
        // Parse saved configs and ensure positions are preserved
        const configs = JSON.parse(savedConfigs);
        configs.forEach(config => {
          // Ensure position is properly loaded from saved config
          if (!config.position) {
            config.position = findFreePosition(this.clocks);
          }
          this.addClock(config);
        });
      }
    } catch (error) {
      console.error('Failed to load saved clocks:', error);
    }
  }

  getFormData(form) {
    const formData = new FormData(form);
    const config = {
      name: formData.get('name'),
      timezoneOffset: parseInt(formData.get('timezoneOffset')),
      hands: [],
      outerScale: {
        divisions: parseInt(formData.get('outerScale.divisions')),
        subdivisions: parseInt(formData.get('outerScale.subdivisions'))
      },
      innerScale: {
        enabled: formData.get('innerScale.enabled') === 'on',
        divisions: parseInt(formData.get('innerScale.divisions')),
        majorDivision: parseInt(formData.get('innerScale.majorDivision'))
      },
      animation: {
        enabled: formData.get('animation.enabled') === 'on',
        smoothSeconds: formData.get('animation.smoothSeconds') === 'on'
      },
      theme: {
        frameColor: formData.get('theme.frameColor') || '#636363',
        backgroundColor: formData.get('theme.backgroundColor') || '#E8E8E8',
        textColor: formData.get('theme.textColor') || '#000000',
        tickColor: formData.get('theme.tickColor') || '#636363',
        centerDotColor: formData.get('theme.centerDotColor') || '#636363'
      }
    };

    // Get hands data
    const handConfigs = form.querySelectorAll('.hand-config');
    handConfigs.forEach((handConfig, index) => {
      config.hands.push({
        rotation: parseInt(handConfig.querySelector(`[name="hands[${index}].rotation"]`).value),
        color: handConfig.querySelector(`[name="hands[${index}].color"]`).value,
        length: parseFloat(handConfig.querySelector(`[name="hands[${index}].length"]`).value),
        smooth: handConfig.querySelector(`[name="hands[${index}].smooth"]`)?.checked || false
      });
    });

    return config;
  }




  initializeModal() {
    const modal = document.getElementById('clockConfigModal');
    const closeBtn = modal.querySelector('.modal__close');
    const cancelBtn = modal.querySelector('.modal__btn--cancel');
    const saveBtn = modal.querySelector('.modal__btn--save');
    const form = document.getElementById('clockConfigForm');
    
    
    saveBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const config = this.getFormData(form);
      if (this.editingClockId) {
        config.id = this.editingClockId;
        this.updateClock(config);
        this.editingClockId = null;
      } else {
        config.id = Date.now().toString();
        this.addClock(config);
      }
      modal.style.display = 'none';
      form.reset();
    });
    
    closeBtn.onclick = () => {
      this.hideModal();
      form.reset();
    };
    
    cancelBtn.onclick = () => {
      this.hideModal();
      form.reset();
    };
    
    window.onclick = (event) => {
      if (event.target === modal) {
	this.hideModal();
        form.reset();
      }
    };
    
    // Initialize inner scale toggle
    const innerScaleToggle = modal.querySelector('[name="innerScale.enabled"]');
    innerScaleToggle.onchange = (e) => {
      document.getElementById('innerScaleConfig').style.display = 
        e.target.checked ? 'grid' : 'none';
    };
  }

}
