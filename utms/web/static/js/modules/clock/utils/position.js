export function findFreePosition(existingClocks, excludeClock = null) {
    const GRID_SIZE = 20;
    const container = document.querySelector('.clocks__grid');
    const bounds = container.getBoundingClientRect();
    
    let x = 0;
    let y = 0;
    
    // Create a map of occupied positions
    const occupiedPositions = new Map();
    existingClocks.forEach((clock, id) => {
        if (clock !== excludeClock) {
            const pos = clock.config.position;
            const size = clock.config.size || 400;
            for (let px = pos.x; px < pos.x + size; px += GRID_SIZE) {
                for (let py = pos.y; py < pos.y + size; py += GRID_SIZE) {
                    occupiedPositions.set(`${px},${py}`, clock);
                }
            }
        }
    });

    // Find first available position
    while (y < bounds.height) {
        const position = { x, y };
        if (!isPositionOccupied(position, occupiedPositions, GRID_SIZE)) {
            return position;
        }
        
        x += GRID_SIZE;
        if (x + 400 > bounds.width) {
            x = 0;
            y += GRID_SIZE;
        }
    }

  return { x: 0, y: 0 }; // Fallback position
}

function isPositionOccupied(position, occupiedPositions, gridSize) {
    const size = 400; // Default size or get from parameter
    for (let px = position.x; px < position.x + size; px += gridSize) {
        for (let py = position.y; py < position.y + size; py += gridSize) {
            if (occupiedPositions.has(`${px},${py}`)) {
                return true;
            }
        }
    }
    return false;
}

export function repositionClocksDuringDrag(draggedClock, newPosition, existingClocks) {
    const affectedClocks = new Set();
    const GRID_SIZE = 20;

    // Check which clocks need to be moved
    for (const [id, clock] of existingClocks) {  // Fix: properly iterate over Map
        if (clock !== draggedClock && checkCollision(newPosition, draggedClock, clock)) {
            affectedClocks.add(clock);
        }
    }

    // Find new positions for affected clocks
    affectedClocks.forEach((clock) => {
        const newPos = findFreePosition(existingClocks, clock);
        clock.config.position = newPos;
        clock.element.style.transform = `translate(${newPos.x}px, ${newPos.y}px)`;
    });

    return affectedClocks.size > 0;
}


function checkCollisionWithPositions(newPosition, width, height, existingPositions) {
  const margin = 10;
    const newBounds = {
        left: newPosition.x,
        right: newPosition.x + width,
        top: newPosition.y,
        bottom: newPosition.y + height
    };

    return existingPositions.some(position => {
        const existingBounds = {
            left: position.x,
            right: position.x + width,
            top: position.y,
            bottom: position.y + height
        };

        return !(newBounds.right + margin < existingBounds.left ||
                newBounds.left > existingBounds.right + margin ||
                newBounds.bottom + margin < existingBounds.top ||
                newBounds.top > existingBounds.bottom + margin);
    });
}

export function checkCollision(newPosition, draggedClock, otherClock) {
    const margin = 10;
    const draggedSize = draggedClock.config.size || 400;
    const otherSize = otherClock.config.size || 400;

    const draggedBounds = {
        left: newPosition.x,
        right: newPosition.x + draggedSize,
        top: newPosition.y,
        bottom: newPosition.y + draggedSize
    };

    const otherBounds = {
        left: otherClock.config.position.x,
        right: otherClock.config.position.x + otherSize,
        top: otherClock.config.position.y,
        bottom: otherClock.config.position.y + otherSize
    };

    return !(draggedBounds.right + margin < otherBounds.left ||
             draggedBounds.left > otherBounds.right + margin ||
             draggedBounds.bottom + margin < otherBounds.top ||
             draggedBounds.top > otherBounds.bottom + margin);
}
