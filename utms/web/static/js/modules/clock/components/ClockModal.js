export class ClockModal {
  constructor(manager) {
    this.manager = manager;
    this.modal = document.getElementById('clockConfigModal');
    this.initializeModal();
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

  show(existingConfig = null) {
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
}
