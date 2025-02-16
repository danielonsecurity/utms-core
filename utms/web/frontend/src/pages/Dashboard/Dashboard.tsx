import React, { useState, useRef, useEffect } from 'react';
import GridLayout from 'react-grid-layout';
import { ClockWidget } from '../../components/widgets/ClockWidget';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const defaultClockConfig = {
    name: "Default Clock",
    timezoneOffset: 0,
    theme: {
	frameColor: '#636363',
	backgroundColor: '#E8E8E8',
	textColor: '#000000',
	tickColor: '#636363',
	centerDotColor: '#636363'
    },
    hands: [
	{ rotation: 43200, color: '#4A4A4A', length: 0.5, smooth: true },
	{ rotation: 3600, color: '#000000', length: 0.8, smooth: true },
	{ rotation: 60, color: '#FF3131', length: 0.9, smooth: true }
    ]
};

interface LayoutItem {
    i: string;
    x: number;
    y: number;
    w: number;
    h: number;
}




export const Dashboard = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const BASE_WIDGET_SIZE = { w: 6, h: 6 };
    const COLUMN_WIDTH = 30; // Smaller column width to make widgets more square

    const [layout, setLayout] = useState<Layout>([
        { i: 'clock1', x: 0, y: 0, w: 6, h: 6 }
    ]);

    const [widgets, setWidgets] = useState([
        { id: 'clock1', type: 'clock', config: defaultClockConfig }
    ]);


    const calculateContainerWidth = () => {
        const viewportWidth = window.innerWidth - 40;
        const maxWidgetRight = layout.reduce((max, item) => 
            Math.max(max, (item.x + item.w) * COLUMN_WIDTH), 0);
        return Math.max(viewportWidth, maxWidgetRight + COLUMN_WIDTH * BASE_WIDGET_SIZE.w);
    };

    const [containerWidth, setContainerWidth] = useState(calculateContainerWidth);

    useEffect(() => {
        const updateWidth = () => {
            setContainerWidth(calculateContainerWidth());
        };

        window.addEventListener('resize', updateWidth);
        return () => window.removeEventListener('resize', updateWidth);
    }, [layout]);

    const findOptimalPosition = (currentLayout: Layout) => {
        const viewportColumns = Math.floor((window.innerWidth - 80) / COLUMN_WIDTH);
        const rows = new Map<number, number>(); // y position -> total width

        // Calculate total width for each row
        currentLayout.forEach(item => {
            const currentWidth = rows.get(item.y) || 0;
            rows.set(item.y, currentWidth + item.w);
        });

        // Find first row with enough space or create new row
        for (const [y, totalWidth] of rows.entries()) {
            if (totalWidth + BASE_WIDGET_SIZE.w <= viewportColumns) {
                const rowItems = currentLayout.filter(item => item.y === y);
                const maxX = Math.max(...rowItems.map(item => item.x + item.w), 0);
                return { x: maxX, y };
            }
        }

        // If no row has space, create new row
        const maxY = Math.max(...Array.from(rows.keys()), -1);
        return { x: 0, y: maxY + BASE_WIDGET_SIZE.h };
    };

const handleAddClock = () => {
    const id = `clock${Date.now()}`;
    
    // Calculate how many widgets fit in a row based on viewport width
    const viewportWidth = window.innerWidth - 40;
    const widgetsPerRow = Math.floor(viewportWidth / ((BASE_WIDGET_SIZE.w * containerWidth / 24) + 20));
    
    // Group widgets by row
    const rowGroups = layout.reduce((groups: {[key: number]: Layout}, item) => {
        const row = item.y;
        if (!groups[row]) groups[row] = [];
        groups[row].push(item);
        return groups;
    }, {});

    // Find first row with available space
    const currentRow = Object.keys(rowGroups).map(Number).sort((a, b) => a - b)[0] || 0;
    const rowWidgets = rowGroups[currentRow] || [];
    
    // Find the rightmost position in the current row
    const rowEndX = rowWidgets.length > 0
        ? Math.max(...rowWidgets.map(item => item.x + item.w))
        : 0;
    
    // Check if there's room in the current row
    const newPosition = {
        x: rowEndX,
        y: currentRow
    };
    
    // If this position would push the widget off screen, start a new row
    if ((newPosition.x + BASE_WIDGET_SIZE.w) * (containerWidth / 24) > viewportWidth) {
        newPosition.x = 0;
        newPosition.y = Math.max(...layout.map(item => item.y + item.h), 0);
    }
    
    setWidgets(prev => [...prev, { 
        id, 
        type: 'clock', 
        config: { ...defaultClockConfig, name: `Clock ${prev.length + 1}` } 
    }]);
    
    setLayout(prev => [...prev, { 
        i: id, 
        ...newPosition,
        ...BASE_WIDGET_SIZE
    }]);
};

    const onResize = (
        layout: Layout,
        oldItem: Layout[0],
        newItem: Layout[0],
        placeholder: Layout[0],
        e: MouseEvent,
        element: HTMLElement
    ) => {
        const widthDiff = newItem.w - oldItem.w;
        
        setLayout(currentLayout => {
            const itemIndex = currentLayout.findIndex(item => item.i === newItem.i);
            const sameRowItems = currentLayout.filter(
                item => item.y === newItem.y && 
                    item.i !== newItem.i &&
                    item.x > oldItem.x
            ).sort((a, b) => a.x - b.x);

            const updatedLayout = [...currentLayout];
            
            // Update resized item
            updatedLayout[itemIndex] = newItem;

            // Shift subsequent items in the same row
            let currentX = newItem.x + newItem.w;
            sameRowItems.forEach(item => {
                const itemIndex = currentLayout.findIndex(i => i.i === item.i);
                updatedLayout[itemIndex] = {
                    ...item,
                    x: currentX
                };
                currentX += item.w;
            });

            return updatedLayout;
        });

        // Update container width if needed
        setContainerWidth(calculateContainerWidth());
    };	

    return (
        <div className="dashboard">
            <div className="dashboard__controls">
            <button className="btn btn--primary" onClick={handleAddClock}>
            <i className="material-icons">add</i>
            Add Clock
        </button>
            </div>
            
            <div className="dashboard__container" ref={containerRef}>
            <GridLayout
        className="dashboard__grid"
        layout={layout}
        cols={24}
        rowHeight={50}
        width={containerWidth}
        onLayoutChange={(newLayout) => setLayout(newLayout)}
        onResize={onResize}
        onResizeStop={onResize}
        draggableHandle=".widget__header"
        margin={[20, 20]}
        containerPadding={[20, 20]}
        isResizable={true}
        resizeHandles={['se']}
        preventCollision={true}
        compactType={null}
        verticalCompact={false}
            >
            {widgets.map(widget => (
                <div key={widget.id}>
                    {widget.type === 'clock' && (
                        <ClockWidget
                        id={widget.id}
                        config={widget.config}
                        onRemove={id => {
                            setWidgets(prev => prev.filter(w => w.id !== id));
                            setLayout(prev => prev.filter(item => item.i !== id));
                        }}
                        onConfigure={() => console.log('Configure:', widget.id)}
                            />
                    )}
                </div>
            ))}
        </GridLayout>
            </div>
            </div>
    );
};
