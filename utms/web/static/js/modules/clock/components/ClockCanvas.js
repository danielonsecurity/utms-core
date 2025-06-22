export class ClockCanvas {
  constructor(clock) {
    this.clock = clock;
    setTimeout(() => {
      this.initialize();
    }, 0);
  }

  initialize() {
    this.element = this.clock.element.querySelector('.clock__canvas');
    this.container = this.clock.element.querySelector('.clock__canvas-container');

    if (!this.element || !this.container) {
      console.error('Canvas elements not found:', {
        canvas: this.element,
        container: this.container,
        clockElement: this.clock.element
      });
      return;
    }

    this.ctx = this.element.getContext('2d');
    this.setupCanvas();
    this.startAnimation();
    
  }

  setupCanvas() {
    if (!this.container) {
      console.error('Container not found for ResizeObserver');
      return;
    }
    // Initialize resize observer
    this.resizeObserver = new ResizeObserver(() => {
      this.setCanvasSize();
    });
    try {
      this.resizeObserver.observe(this.container);
    } catch (error) {
      console.error('Failed to setup ResizeObserver:', error);
    }

    // Initial size setup
    this.setCanvasSize();
 
  }

  setCanvasSize() {
    const container = this.container;
    const size = container.offsetWidth;

    this.element.width = size;
    this.element.height = size;

    this.center = size / 2;
    this.radius = (size / 2) * 0.9; // 90% of half width
    
    this.drawClock();
  }

  startAnimation() {
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

  drawClock() {
    this.ctx.clearRect(0, 0, this.element.width, this.element.height);
    
    this.drawFrame();
    this.drawScales();
    this.drawHands();
    this.drawCenterDot();
  }

  drawFrame() {
    const { frameColor, backgroundColor } = this.clock.theme;

    // Outer circle
    this.ctx.beginPath();
    this.ctx.arc(this.center, this.center, this.radius + 5, 0, 2 * Math.PI);
    this.ctx.strokeStyle = frameColor;
    this.ctx.lineWidth = 5;
    this.ctx.stroke();

    // Inner circle
    this.ctx.beginPath();
    this.ctx.arc(this.center, this.center, this.radius, 0, 2 * Math.PI);
    this.ctx.fillStyle = backgroundColor;
    this.ctx.fill();
  }

  drawScales() {
    this.drawOuterScale();
    if (this.clock.config.innerScale?.enabled) {
      this.drawInnerScale();
    }
  }

  drawOuterScale() {
    const { divisions, subdivisions } = this.clock.config.outerScale;
    const { tickColor, textColor } = this.clock.theme;
    
    for (let i = 0; i < divisions; i++) {
      const angle = (i * 2 * Math.PI) / divisions;
      
      // Draw major tick
      this.drawTick(angle, true, tickColor);
      
      // Draw number
      this.drawNumber(i, divisions, angle, textColor);

      // Draw subdivisions
      for (let j = 1; j < subdivisions; j++) {
        const subAngle = angle + (j * 2 * Math.PI) / (divisions * subdivisions);
        this.drawTick(subAngle, false, tickColor);
      }
    }
  }

  drawInnerScale() {
    const { divisions, majorDivision } = this.clock.config.innerScale;
    const { tickColor, textColor } = this.clock.theme;
    const innerRadius = this.radius * 0.7;

    for (let i = 0; i < divisions; i++) {
      const angle = (i * 2 * Math.PI) / divisions;
      const isMajor = i % majorDivision === 0;

      const tickStart = innerRadius;
      const tickEnd = innerRadius - (isMajor ? 15 : 5);
      
      this.drawRadialLine(angle, tickStart, tickEnd, tickColor, isMajor ? 2 : 1);

      if (isMajor) {
        this.drawInnerNumber(i, angle, tickEnd - 10, textColor);
      }
    }
  }

  drawHands() {
    const seconds = this.getSecondsSinceMidnight();
    
    this.clock.config.hands.forEach(hand => {
      let timeValue = seconds;
      if (!hand.smooth) {
        timeValue = Math.floor(timeValue);
      }
      const angle = (2 * Math.PI * timeValue) / hand.rotation;
      this.drawHand(angle, hand);
    });
  }

  getSecondsSinceMidnight() {
    const now = new Date();
    const offset = this.clock.config.timezoneOffset || 0;
    
    if (this.clock.config.animation?.smoothSeconds) {
      const milliseconds = now.getUTCMilliseconds() / 1000;
      return ((now.getUTCHours() + offset) * 3600 + 
              now.getUTCMinutes() * 60 + 
              now.getUTCSeconds() +
              milliseconds);
    }
    
    return ((now.getUTCHours() + offset) * 3600 + 
            now.getUTCMinutes() * 60 + 
            now.getUTCSeconds());
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

    // Draw hand shape
    this.ctx.beginPath();
    this.ctx.moveTo(tip.x, tip.y);
    this.ctx.lineTo(middle.x + middleOffset.x, middle.y + middleOffset.y);
    this.ctx.lineTo(this.center + middleOffset.x, this.center + middleOffset.y);
    this.ctx.lineTo(this.center - middleOffset.x, this.center - middleOffset.y);
    this.ctx.lineTo(middle.x - middleOffset.x, middle.y - middleOffset.y);
    this.ctx.closePath();

    this.ctx.fillStyle = hand.color;
    this.ctx.fill();
  }

  drawCenterDot() {
    this.ctx.beginPath();
    this.ctx.arc(this.center, this.center, 7, 0, 2 * Math.PI);
    this.ctx.fillStyle = this.clock.theme.centerDotColor;
    this.ctx.fill();
  }

  // Helper methods
  drawTick(angle, isMajor, color) {
    const tickStart = this.radius;
    const tickEnd = this.radius - (isMajor ? 10 : 5);
    this.drawRadialLine(angle, tickStart, tickEnd, color, isMajor ? 2 : 1);
  }

  drawRadialLine(angle, startRadius, endRadius, color, width) {
    const startX = this.center + startRadius * Math.sin(angle);
    const startY = this.center - startRadius * Math.cos(angle);
    const endX = this.center + endRadius * Math.sin(angle);
    const endY = this.center - endRadius * Math.cos(angle);

    this.ctx.beginPath();
    this.ctx.moveTo(startX, startY);
    this.ctx.lineTo(endX, endY);
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = width;
    this.ctx.stroke();
  }

  drawNumber(num, total, angle, color) {
    const numberRadius = this.radius - 25;
    const x = this.center + numberRadius * Math.sin(angle);
    const y = this.center - numberRadius * Math.cos(angle);

    this.ctx.font = '16px Orbitron';
    this.ctx.fillStyle = color;
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(num.toString(), x, y);
  }

  drawInnerNumber(num, angle, radius, color) {
    const x = this.center + radius * Math.sin(angle);
    const y = this.center - radius * Math.cos(angle);

    this.ctx.font = '8px Orbitron';
    this.ctx.fillStyle = color;
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(num.toString(), x, y);
  }



  destroy() {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
    this.resizeObserver.disconnect();


  }
}
