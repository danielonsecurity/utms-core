export class ClockResize {
  constructor(clock) {
    this.clock = clock;
    this.element = clock.element;
    this.handle = this.element.querySelector('.clock__resize-handle');
    this.GRID_SIZE = 20;
    this.MIN_SIZE = 300;
    this.MAX_SIZE = 600;
    this.setupResize();
  }

  snapToGrid(size) {
    return Math.round(size / this.GRID_SIZE) * this.GRID_SIZE;
  }

  constrainSize(size) {
    return Math.max(this.MIN_SIZE, Math.min(this.MAX_SIZE, size));
  }


  setupResize() {
    let startX, startY, startWidth;
    
    const startResize = (e) => {
      e.preventDefault();
      const point = e.touches ? e.touches[0] : e;
      startX = point.clientX;
      startY = point.clientY;
      startWidth = this.element.offsetWidth;
      
      document.addEventListener(e.touches ? 'touchmove' : 'mousemove', resize);
      document.addEventListener(e.touches ? 'touchend' : 'mouseup', stopResize);
      this.element.classList.add('resizing');
    };

    const resize = (e) => {
      e.preventDefault();
      const point = e.touches ? e.touches[0] : e;
      const delta = point.clientX - startX;
      const newWidth = startWidth + delta;
      const snappedSize = this.snapToGrid(newWidth);
      const constrainedSize = this.constrainSize(snappedSize);
      
      // Check if new size would cause collisions
      const wouldCollide = window.clockManager.checkCollisionWithNewSize(
        this.clock,
        constrainedSize
      );

      if (!wouldCollide) {
        this.element.style.width = `${constrainedSize}px`;
        this.clock.canvas.setCanvasSize();
      }
    };

    const stopResize = () => {
      document.removeEventListener('mousemove', resize);
      document.removeEventListener('mouseup', stopResize);
      document.removeEventListener('touchmove', resize);
      document.removeEventListener('touchend', stopResize);
      
      this.element.classList.remove('resizing');
      
      // Save the new size in the clock's config
      this.clock.config.size = this.element.offsetWidth;
      window.clockManager.saveClocks();
    };

    this.handle.addEventListener('mousedown', startResize);
    this.handle.addEventListener('touchstart', startResize);

    this.resizeListeners = { startResize };
  }

  destroy() {
    if (this.resizeListeners) {
      this.handle.removeEventListener('mousedown', this.resizeListeners.startResize);
      this.handle.removeEventListener('touchstart', this.resizeListeners.startResize);
      this.resizeListeners = null;
    }
  }
}
