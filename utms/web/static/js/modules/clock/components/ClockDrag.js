import { repositionClocksDuringDrag } from '../utils/position.js';

export class ClockDrag {
  constructor(clock) {
    this.clock = clock;
    this.element = clock.element;
    this.position = clock.config.position;
    this.setupDragging();
    this.updatePosition();
  }

  setupDragging() {
    const header = this.element.querySelector('.clock__header');
    let startX, startY;
    let originalX, originalY;
    
    const onMouseDown = (e) => {
      // Only start drag if clicking the header (not buttons)
      if (!e.target.closest('.clock__controls')) {
        e.preventDefault();
        
        // Store the initial positions
        startX = e.clientX;
        startY = e.clientY;
        originalX = this.position.x;
        originalY = this.position.y;

        // Add dragging class
        this.element.classList.add('dragging');

        // Add event listeners for drag and end
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);

        // Log start of drag for debugging
        console.log('Drag started:', { startX, startY, originalX, originalY });
      }
    };

    const onMouseMove = (e) => {
      e.preventDefault();
      
      // Calculate new position
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      
      const newX = originalX + dx;
      const newY = originalY + dy;

      const gridSize = 20;
      const snappedX = Math.round(newX / gridSize) * gridSize;
      const snappedY = Math.round(newY / gridSize) * gridSize;

      // Get container bounds
      const container = document.querySelector('.clocks__grid');
      const containerBounds = container.getBoundingClientRect();
      const clockBounds = this.element.getBoundingClientRect();

      // Constrain to container
      const maxX = containerBounds.width - clockBounds.width;
      const maxY = Math.max(containerBounds.height - clockBounds.height, 0);
      
      const constrainedX = Math.max(0, Math.min(snappedX, maxX));
      const constrainedY = Math.max(0, Math.min(snappedY, maxY));

      const newPosition = { x: constrainedX, y: constrainedY };
      
      // Check if we need to reposition other clocks
      repositionClocksDuringDrag(this.clock, newPosition, window.clockManager.clocks);

      // Update position
      this.position = newPosition;
      this.updatePosition();

      // Update the clock's config position as well
      this.clock.config.position = this.position;
    };

    const onMouseUp = (e) => {
      // Remove dragging class
      this.element.classList.remove('dragging');

      // Remove event listeners
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);

      // Save the final position
      window.clockManager.saveClocks();
    };

    // Add initial mousedown listener
    header.addEventListener('mousedown', onMouseDown);

    // Store event listeners for cleanup
    this.dragListeners = {
      onMouseDown
    };
  }

  updatePosition() {
    this.element.style.transform = `translate(${this.position.x}px, ${this.position.y}px)`;
  }

  destroy() {
    if (this.dragListeners) {
      const header = this.element.querySelector('.clock__header');
      if (header) {
        header.removeEventListener('mousedown', this.dragListeners.onMouseDown);
      }
      this.dragListeners = null;
    }
  }
}
