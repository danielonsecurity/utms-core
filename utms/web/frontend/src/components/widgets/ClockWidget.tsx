import React, { useEffect, useRef } from 'react';
import { BaseWidget, WidgetProps } from './BaseWidget';

interface ClockConfig {
    name: string;
    timezoneOffset: number;
    theme: {
	frameColor: string;
	backgroundColor: string;
	textColor: string;
	tickColor: string;
	centerDotColor: string;
    };
    hands: Array<{
	rotation: number;
	color: string;
	length: number;
	smooth: boolean;
    }>;
}

interface ClockWidgetProps extends Omit<WidgetProps, 'title'> {
    config: ClockConfig;
}

export const ClockWidget: React.FC<ClockWidgetProps> = ({ 
    id, 
    config, 
    onRemove, 
    onConfigure 
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const animationFrameRef = useRef<number>();

    useEffect(() => {
	const canvas = canvasRef.current;
	const container = containerRef.current;
	if (!canvas || !container) return;

	const ctx = canvas.getContext('2d');
	if (!ctx) return;

        const resizeCanvas = () => {
            const containerRect = container.getBoundingClientRect();
            const size = Math.min(containerRect.width, containerRect.height);
            
            // Set canvas size
            canvas.width = size;
            canvas.height = size;

            // Set the CSS dimensions to match
            canvas.style.width = `${size}px`;
            canvas.style.height = `${size}px`;

	    canvas.style.transform = 'none';

        };

	const drawClock = () => {
	    const { width, height } = canvas;
	    const center = width / 2;
	    const radius = (Math.min(width, height) / 2) * 0.9;

	    // Clear canvas
	    ctx.clearRect(0, 0, width, height);

	    // Draw clock face
	    ctx.beginPath();
	    ctx.arc(center, center, radius, 0, 2 * Math.PI);
	    ctx.fillStyle = config.theme.backgroundColor;
	    ctx.fill();
	    ctx.strokeStyle = config.theme.frameColor;
	    ctx.lineWidth = 2;
	    ctx.stroke();

	    // Draw hour marks
	    for (let i = 0; i < 12; i++) {
		const angle = (i * Math.PI) / 6;
		ctx.beginPath();
		ctx.moveTo(
		    center + radius * 0.9 * Math.cos(angle),
		    center + radius * 0.9 * Math.sin(angle)
		);
		ctx.lineTo(
		    center + radius * Math.cos(angle),
		    center + radius * Math.sin(angle)
		);
		ctx.strokeStyle = config.theme.tickColor;
		ctx.lineWidth = 2;
		ctx.stroke();
	    }

	    // Get current time
	    const now = new Date();
	    const hours = now.getHours() % 12;
	    const minutes = now.getMinutes();
	    const seconds = now.getSeconds();

	    // Draw hands
	    config.hands.forEach(hand => {
		let angle;
		if (hand.rotation === 43200) { // Hour hand
		    angle = (hours * 30 + minutes / 2) * Math.PI / 180;
		} else if (hand.rotation === 3600) { // Minute hand
		    angle = (minutes * 6 + seconds / 10) * Math.PI / 180;
		} else { // Second hand
		    angle = seconds * 6 * Math.PI / 180;
		}

		ctx.beginPath();
		ctx.moveTo(center, center);
		ctx.lineTo(
		    center + radius * hand.length * Math.sin(angle),
		    center - radius * hand.length * Math.cos(angle)
		);
		ctx.strokeStyle = hand.color;
		ctx.lineWidth = hand.rotation === 60 ? 1 : 2;
		ctx.stroke();
	    });

	    // Draw center dot
	    ctx.beginPath();
	    ctx.arc(center, center, 3, 0, 2 * Math.PI);
	    ctx.fillStyle = config.theme.centerDotColor;
	    ctx.fill();

	    animationFrameRef.current = requestAnimationFrame(drawClock);
	};

	const resizeObserver = new ResizeObserver(() => {
	    resizeCanvas();
	    drawClock();
	});

	resizeObserver.observe(container);
	
	// Initial draw
	resizeCanvas();
	drawClock();

        // Animation loop
        const animate = () => {
            drawClock();
            animationFrameRef.current = requestAnimationFrame(animate);
        };
        animate();

	return () => {
	    if (animationFrameRef.current) {
		cancelAnimationFrame(animationFrameRef.current);
	    }
	    resizeObserver.disconnect();
	};
    }, [config]);

    return (
        <div 
            ref={containerRef} 
            style={{ 
                width: '100%', 
                height: '100%', 
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
                boxSizing: 'border-box'
            }}
        >
            <canvas
                ref={canvasRef}
                style={{
                    display: 'block',
		    flexShrink: 0
                }}
            />
        </div>
    );

};
