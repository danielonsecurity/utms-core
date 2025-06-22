import { ClockDrag } from './components/ClockDrag.js';
import { ClockCanvas } from './components/ClockCanvas.js';
import { ClockResize } from './components/ClockResize.js';
import { validateConfig } from './utils/config.js';
import { getDefaultTheme } from './utils/theme.js';

export class Clock {
  constructor(config) {
    validateConfig(config);
    
    this.config = config;
    this.theme = config.theme || getDefaultTheme();

    this.element = this.createClockElement();
    this.initializeComponents();


  }

  initializeComponents() {
    this.canvas = new ClockCanvas(this);
    this.drag = new ClockDrag(this);
    this.resize = new ClockResize(this);

  }

  createClockElement() {
    const clockDiv = document.createElement('div');
    clockDiv.className = 'clock';
    // Set initial size if it exists in config
    if (this.config.size) {
      clockDiv.style.width = `${this.config.size}px`;
    }
    clockDiv.innerHTML = `
      <div class="clock__header">
        <h3 class="clock__title">${this.config.name}</h3>
        <div class="clock__controls">
          <button class="btn btn--icon btn--edit" title="Edit Clock">
            <i class="material-icons">edit</i>
          </button>
          <button class="btn btn--icon btn--delete" title="Delete Clock">
            <i class="material-icons">delete</i>
          </button>
        </div>
      </div>
      <div class="clock__canvas-container">
        <canvas class="clock__canvas"></canvas>
      </div>
      <div class="clock__resize-handle">
        <i class="material-icons">drag_handle</i>
      </div>
    `;

    this.setupEventListeners(clockDiv);
    return clockDiv;
  }

  setupEventListeners(clockDiv) {
    clockDiv.querySelector('.btn--edit').addEventListener('click', () => {
      this.editClock();
    });
    
    clockDiv.querySelector('.btn--delete').addEventListener('click', () => {
      this.deleteClock();
    });
  }



  setCanvasSize() {
    const container = this.canvas.parentElement;
    const size = container.offsetWidth;

    this.canvas.width = size;
    this.canvas.height = size;

    this.center = size / 2;
    this.radius = (size / 2) * 0.9;
    this.drawClock();
  }

  startClock() {
    let lastTime = 0;
    const fps = 60;
    const interval = 1000 / fps;

    const updateClock = (timestamp) => {
      if (!lastTime || timestamp - lastTime >= interval) {
        this.drawClock();
        lastTime = timestamp;
      }
      this.animationFrame = requestAnimationFrame(updateClock);
    };
    this.animationFrame = requestAnimationFrame(updateClock);
  }

  getSecondsSinceMidnight() {
    const now = new Date();
    const offset = this.config.timezoneOffset || 0;
    
    if (this.animation.smoothSeconds) {
      // For smooth movement, calculate fractional seconds
      const milliseconds = now.getUTCMilliseconds() / 1000;
      return ((now.getUTCHours() + offset) * 3600 + 
              now.getUTCMinutes() * 60 + 
              now.getUTCSeconds() +
              milliseconds);
    } else {
      // For discrete movement
      return ((now.getUTCHours() + offset) * 3600 + 
              now.getUTCMinutes() * 60 + 
              now.getUTCSeconds());
    }
  }

  drawClock() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    this.drawFrame();
    this.drawOuterScale();
    if (this.config.innerScale?.enabled) {
      this.drawInnerScale();
    }
    
    const seconds = this.getSecondsSinceMidnight();
    this.drawHands(seconds);
    this.drawCenterDot();
  }

  drawFrame() {
    this.ctx.beginPath();
    this.ctx.arc(this.center, this.center, this.radius + 5, 0, 2 * Math.PI);
    this.ctx.strokeStyle = this.theme.frameColor;
    this.ctx.lineWidth = 5;
    this.ctx.stroke();

    this.ctx.beginPath();
    this.ctx.arc(this.center, this.center, this.radius, 0, 2 * Math.PI);
    this.ctx.fillStyle = this.theme.backgroundColor;
    this.ctx.fill();
  }

  drawOuterScale() {
    const divisions = this.config.outerScale.divisions;
    const subdivisions = this.config.outerScale.subdivisions;
    
    for (let i = 0; i < divisions; i++) {
      // Draw major tick and number
      const angle = (i * 2 * Math.PI) / divisions;
      this.drawTick(angle, true);
      this.drawNumber(i, divisions, angle);
      
      // Draw subdivisions
      for (let j = 1; j < subdivisions; j++) {
        const subAngle = angle + (j * 2 * Math.PI) / (divisions * subdivisions);
        this.drawTick(subAngle, false);
      }
    }
  }
  
  drawInnerScale() {
    const { divisions, majorDivision } = this.config.innerScale;
    const innerRadius = this.radius * 0.7;
    
    for (let i = 0; i < divisions; i++) {
      const angle = (i * 2 * Math.PI) / divisions;
      const isMajor = i % majorDivision === 0;
      
      // Draw tick
      const tickStart = innerRadius;
      const tickEnd = innerRadius - (isMajor ? 15 : 5);
      
      const startX = this.center + tickStart * Math.sin(angle);
      const startY = this.center - tickStart * Math.cos(angle);
      const endX = this.center + tickEnd * Math.sin(angle);
      const endY = this.center - tickEnd * Math.cos(angle);
      
      this.ctx.beginPath();
      this.ctx.moveTo(startX, startY);
      this.ctx.lineTo(endX, endY);
      this.ctx.strokeStyle = this.theme.frameColor;
      this.ctx.lineWidth = isMajor ? 2 : 1;
      this.ctx.stroke();
      
      // Draw number for major ticks
      if (isMajor) {
        const numberRadius = tickEnd - 10;
        const numberX = this.center + numberRadius * Math.sin(angle);
        const numberY = this.center - numberRadius * Math.cos(angle);
	
        this.ctx.font = '8px Orbitron';
        this.ctx.fillStyle = this.theme.textColor;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(i.toString(), numberX, numberY);
      }
    }
  }
  
  drawTick(angle, isMajor) {
    const tickStart = this.radius;
    const tickEnd = this.radius - (isMajor ? 10 : 5);
    
    const startX = this.center + tickStart * Math.sin(angle);
    const startY = this.center - tickStart * Math.cos(angle);
    const endX = this.center + tickEnd * Math.sin(angle);
    const endY = this.center - tickEnd * Math.cos(angle);
    
    this.ctx.beginPath();
    this.ctx.moveTo(startX, startY);
    this.ctx.lineTo(endX, endY);
    this.ctx.strokeStyle = this.theme.frameColor;
    this.ctx.lineWidth = isMajor ? 2 : 1;
    this.ctx.stroke();
  }
  
  drawNumber(i, divisions, angle) {
    const numberRadius = this.radius - 25;
    const numberX = this.center + numberRadius * Math.sin(angle);
    const numberY = this.center - numberRadius * Math.cos(angle);
    
    this.ctx.font = '16px Orbitron';
    this.ctx.fillStyle = this.theme.textColor;
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(i.toString(), numberX, numberY);
  }
  
  drawHands(seconds) {
    this.config.hands.forEach(hand => {
      const angle = (2 * Math.PI * seconds) / hand.rotation;
      this.drawHand(angle, hand);
    });
  }
  
  drawHand(angle, hand) {
    const length = this.radius * hand.length;
    const baseWidth = hand.baseWidth || (hand.length > 0.7 ? 3 : hand.length > 0.5 ? 10 : 15);
    
    // Calculate hand geometry
    const tip = {
      x: this.center + length * Math.sin(angle),
      y: this.center - length * Math.cos(angle)
    };
    
    const middle = {
      x: this.center + (length / 2) * Math.sin(angle),
      y: this.center - (length / 2) * Math.cos(angle)
    };
    
    const middleOffset = {
      x: (baseWidth / 2) * Math.cos(angle),
      y: (baseWidth / 2) * Math.sin(angle)
    };
    
    const baseOffset = {
      x: (baseWidth / 4) * Math.cos(angle),
      y: (baseWidth / 4) * Math.sin(angle)
    };
    
    // Draw hand
    this.ctx.beginPath();
    this.ctx.moveTo(tip.x, tip.y);
    this.ctx.lineTo(middle.x + middleOffset.x, middle.y + middleOffset.y);
    this.ctx.lineTo(this.center + baseOffset.x, this.center + baseOffset.y);
    this.ctx.lineTo(this.center - baseOffset.x, this.center - baseOffset.y);
    this.ctx.lineTo(middle.x - middleOffset.x, middle.y - middleOffset.y);
    this.ctx.closePath();
    
    this.ctx.fillStyle = hand.color;
    this.ctx.fill();
  }
  
  drawCenterDot() {
    this.ctx.beginPath();
    this.ctx.arc(this.center, this.center, 7, 0, 2 * Math.PI);
    this.ctx.fillStyle = this.theme.frameColor;
    this.ctx.fill();
  }
  
  destroy() {
    this.canvas.destroy();
    this.drag.destroy();
    this.resize.destroy();

    // Remove event listeners
    const editBtn = this.element.querySelector('.btn--edit');
    const deleteBtn = this.element.querySelector('.btn--delete');
    
    editBtn.removeEventListener('click', this.editClock);
    deleteBtn.removeEventListener('click', this.deleteClock);
    this.element.remove();

  }

  editClock() {
    window.clockManager.showClockModal(this.config);
  }

  deleteClock() {
    if (confirm('Are you sure you want to delete this clock?')) {
      window.clockManager.deleteClock(this.config.id);
    }
  }




}
