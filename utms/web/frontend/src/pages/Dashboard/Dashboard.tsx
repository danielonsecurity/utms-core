import React, { useEffect, useRef, useState } from "react";
import { GridStack } from "gridstack";
import "gridstack/dist/gridstack.min.css";

interface WidgetData {
  id: string;
  title: string;
}

export const Dashboard = () => {
  const gridRef = useRef<HTMLDivElement>(null);
  const grid = useRef<GridStack | null>(null);
  const [widgets, setWidgets] = useState<WidgetData[]>(() => {
    const saved = localStorage.getItem("dashboard-widgets");
    return saved ? JSON.parse(saved) : [];
  });
  const restoredRef = useRef(false);
  const [gridWidth, setGridWidth] = useState(24); // Start with 12 columns
  const BASE_COLUMN_WIDTH = 100;
  const CELL_WIDTH = 50;
  const COLUMN_WIDTH = 50;
  const MIN_COLUMNS = 12;
  const MAX_COLUMNS = 100;
  const MARGIN = 10;

  const INITIAL_COLUMNS = MIN_COLUMNS;
  const [containerWidth, setContainerWidth] = useState(
    INITIAL_COLUMNS * COLUMN_WIDTH,
  );

  const resizeTimeoutRef = useRef<NodeJS.Timeout>();

  const getNextWidgetId = () => {
    const savedLayout = localStorage.getItem("dashboard-layout");
    if (!savedLayout) return 0;

    try {
      const layout = JSON.parse(savedLayout);
      const ids = layout.map((item) => {
        const match = item.id.match(/widget-(\d+)/);
        return match ? parseInt(match[1]) : 0;
      });

      console.log("Existing widget IDs:", ids);
      const maxId = Math.max(...ids, -1);
      console.log("Next widget ID will be:", maxId + 1);
      return maxId + 1;
    } catch (error) {
      console.warn("Failed to parse layout for ID generation:", error);
      return 0;
    }
  };

  const findOptimalPosition = (
    nodes: any[],
    widgetWidth: number = 4,
    widgetHeight: number = 4,
  ) => {
    console.log("Finding optimal position for new widget");

    const maxX = nodes.reduce((max, node) => Math.max(max, node.x + node.w), 0);

    // Allow placement beyond current width
    if (maxX + widgetWidth <= gridWidth) {
      console.log("Found space in current row at:", maxX);
      return { x: maxX, y: 0 };
    }

    // If there's space in the current row (within 12 columns)
    if (maxX + widgetWidth <= 12) {
      console.log("Found space in current row at:", maxX);
      return { x: maxX, y: 0 };
    }

    // If no space in first row, find first available space
    for (let y = 0; y < 20; y++) {
      for (let x = 0; x < 12 - widgetWidth + 1; x++) {
        const collision = nodes.some(
          (node) =>
            x < node.x + node.w &&
            x + widgetWidth > node.x &&
            y < node.y + node.h &&
            y + widgetHeight > node.y,
        );

        if (!collision) {
          console.log("Found space at:", { x, y });
          return { x, y };
        }
      }
    }

    // If no space found, return 0,0 (GridStack will handle stacking)
    console.log("No optimal position found, defaulting to 0,0");
    return { x: 0, y: 0 };
  };

  const createWidgetContent = (widget: WidgetData, gridItem: HTMLElement) => {
    console.log("Creating content for widget:", widget.id);
    const contentDiv = gridItem.querySelector(".grid-stack-item-content");
    console.log("Found content div:", contentDiv);

    if (!contentDiv) {
      console.warn("No content div found for widget:", widget.id);
      return;
    }

    if (contentDiv.children.length > 0) {
      console.log("Content already exists for widget:", widget.id);
      return;
    }

    if (contentDiv) {
      contentDiv.innerHTML = `
<div class="widget-header">
<span>${widget.title}</span>
<button class="widget-close" data-widget-id="${widget.id}">×</button>
</div>
<div class="widget-content">
Content for ${widget.title}
</div>
`;

      // Attach close handler
      const closeBtn = contentDiv.querySelector(".widget-close");
      if (closeBtn) {
        closeBtn.addEventListener("click", () => {
          console.log("Removing widget:", widget.id);
          grid.current?.removeWidget(gridItem);
          setWidgets((prev) => prev.filter((w) => w.id !== widget.id));
          const layout = grid.current?.save();
          localStorage.setItem("dashboard-layout", JSON.stringify(layout));
        });
      }
    }
  };

  useEffect(() => {
    localStorage.setItem("dashboard-widgets", JSON.stringify(widgets));
  }, [widgets]);

  let isUpdating = false;

  useEffect(() => {
    if (!gridRef.current) {
      console.log("No grid ref found");
      return;
    }
    const columnCount = Math.max(
      MIN_COLUMNS,
      Math.floor(containerWidth / COLUMN_WIDTH),
    );
    console.log("Initializing grid with:", {
      containerWidth,
      columnCount,
      columnWidth: COLUMN_WIDTH,
    });

    grid.current = GridStack.init(
      {
        margin: MARGIN,
        cellHeight: 50,
        minRow: 1,
        float: true,
        resizable: true,
        draggable: true,
        disableOneColumnMode: true,
        column: INITIAL_COLUMNS,
        cellWidth: CELL_WIDTH,
      },
      gridRef.current,
    );

    let updateTimeout: NodeJS.Timeout;

    const handleGridUpdate = (event: any) => {
      console.log("Grid update event:", event?.type);

      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }

      resizeTimeoutRef.current = setTimeout(() => {
        if (!grid.current) return;

        const nodes = grid.current.engine.nodes;
        const maxX = nodes.reduce((max, node) => {
          const rightEdge = node.x + node.w;
          console.log(
            `Node ${node.id}: x=${node.x}, w=${node.w}, rightEdge=${rightEdge}`,
          );
          return Math.max(max, rightEdge);
        }, 0);

        console.log("Current layout:", {
          maxX,
          currentColumns: gridWidth,
          currentWidth: containerWidth,
        });

        const MAX_COLUMNS = 50; // Set a reasonable maximum
        const currentWidgetWidth = Math.max(...nodes.map((node) => node.w));

        // Only expand if we actually need more space
        if (maxX > gridWidth || currentWidgetWidth > gridWidth) {
          // Calculate needed columns with constraints
          const neededColumns = Math.min(
            Math.max(MIN_COLUMNS, maxX + 2), // Reduced buffer from 4 to 2
            MAX_COLUMNS,
          );

          // Only update if we actually need more columns
          if (neededColumns > gridWidth) {
            console.log("Updating dimensions:", {
              oldColumns: gridWidth,
              newColumns: neededColumns,
              oldWidth: containerWidth,
              reason: maxX > gridWidth ? "position" : "width",
            });

            const newWidth = neededColumns * (COLUMN_WIDTH + MARGIN) + MARGIN;

            // Prevent updates that would make the grid smaller
            if (newWidth > containerWidth) {
              setGridWidth(neededColumns);
              setContainerWidth(newWidth);
              grid.current.column(neededColumns);
            }
          }
        }

        // Save layout
        const layout = grid.current.save();
        localStorage.setItem("dashboard-layout", JSON.stringify(layout));
      }, 100);
    };
    // Attach to all relevant events
    grid.current.on("change", handleGridUpdate);
    grid.current.on("resize", handleGridUpdate);
    grid.current.on("resizestop", handleGridUpdate);
    grid.current.on("dragstop", handleGridUpdate);

    const layout = grid.current?.save();
    localStorage.setItem("dashboard-layout", JSON.stringify(layout));

    // load saved layout
    if (!restoredRef.current && widgets.length > 0) {
      const savedLayout = localStorage.getItem("dashboard-layout");
      if (savedLayout) {
        try {
          console.log("Loading saved layout");
          const layout = JSON.parse(savedLayout);
          grid.current.load(layout);

          // Recreate widget contents
          widgets.forEach((widget) => {
            console.log("Restoring widget content:", widget.id);
            const gridItem = document.querySelector(`[gs-id="${widget.id}"]`);
            if (gridItem) {
              createWidgetContent(widget, gridItem as HTMLElement);
            }
          });
        } catch (error) {
          console.warn("Failed to load saved layout:", error);
        }
      } else {
        console.log("No saved layout found");
      }
      restoredRef.current = true;
    }
    return () => {
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
      if (grid.current) {
        grid.current.off("change", handleGridUpdate);
        grid.current.off("resize", handleGridUpdate);
        grid.current.off("resizestop", handleGridUpdate);
        grid.current.off("dragstop", handleGridUpdate);
        grid.current.destroy(false);
        grid.current = null;
      }
    };
  }, [widgets.length]);

  const addWidget = () => {
    console.log("Adding widget");
    if (!grid.current) {
      console.log("No grid instance found");
      return;
    }
    const nodes = grid.current.engine.nodes;
    console.log("Current grid nodes:", nodes);

    const { x: bestX, y: bestY } = findOptimalPosition(nodes);
    const nextId = getNextWidgetId();
    const newWidget: WidgetData = {
      id: `widget-${nextId}`,
      title: `Widget ${nextId}`,
    };
    console.log("Adding widget:", newWidget, "at position:", {
      x: bestX,
      y: bestY,
    });

    const widget = grid.current.addWidget({
      w: 8,
      h: 8,
      x: bestX * 2,
      y: bestY * 2,
      id: newWidget.id,
      autoPosition: false,
    });
    console.log("Widget added:", newWidget);
    createWidgetContent(newWidget, widget);
    setWidgets((prev) => [...prev, newWidget]);

    // Save layout after adding new widget
    const layout = grid.current.save();
    localStorage.setItem("dashboard-layout", JSON.stringify(layout));
  };

  // Update the return JSX, move the button outside the header
  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <div
        style={{
          padding: "16px",
          borderBottom: "1px solid #ddd",
          background: "#f5f5f5",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          position: "sticky",
          top: 0,
          zIndex: 1,
        }}
      >
        <div>Dashboard</div>
      </div>
      <div
        style={{
          flex: 1,
          padding: "16px",
          overflowX: "auto",
          overflowY: "auto",
          position: "relative", // Add this
        }}
      >
        <div
          ref={gridRef}
          className="grid-stack"
          style={{
            width: `${containerWidth}px`,
            minHeight: "100%",
          }}
        ></div>
        <button
          onClick={addWidget}
          style={{
            position: "fixed",
            bottom: "32px",
            right: "32px",
            width: "56px",
            height: "56px",
            borderRadius: "28px",
            backgroundColor: "#1976d2",
            color: "white",
            border: "none",
            fontSize: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            boxShadow:
              "0 3px 5px -1px rgba(0,0,0,.2), 0 6px 10px 0 rgba(0,0,0,.14), 0 1px 18px 0 rgba(0,0,0,.12)",
            transition: "background-color 0.2s",
            zIndex: 2,
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = "#1565c0")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = "#1976d2")
          }
        >
          +
        </button>
      </div>
    </div>
  );
};
