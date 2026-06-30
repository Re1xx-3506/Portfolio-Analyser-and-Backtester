import React, { useState, useRef, useEffect } from "react";

interface DataPoint {
  date: string;
  [key: string]: any;
}

interface InteractiveChartProps {
  data: DataPoint[];
  keys: string[];
  colors: { [key: string]: string };
  labels: { [key: string]: string };
  formatY: (val: number) => string;
  height?: number;
}

export const InteractiveChart: React.FC<InteractiveChartProps> = ({
  data,
  keys,
  colors,
  labels,
  formatY,
  height = 360,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);

  // Resize handler
  useEffect(() => {
    if (!containerRef.current) return;
    const handleResize = () => {
      setWidth(containerRef.current?.getBoundingClientRect().width || 800);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  if (!data || data.length === 0) {
    return (
      <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center", color: "#6b7280" }}>
        No data available for chart.
      </div>
    );
  }

  // Margin settings
  const margin = { top: 20, right: 30, bottom: 40, left: 65 };
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;

  // Extract all values for scaling
  const allValues: number[] = [];
  data.forEach((d) => {
    keys.forEach((k) => {
      const val = d[k];
      if (val !== undefined && val !== null && !isNaN(val)) {
        allValues.push(val);
      }
    });
  });

  const minVal = allValues.length ? Math.min(...allValues) : 0;
  const maxVal = allValues.length ? Math.max(...allValues) : 100;
  
  // Padding for visual buffer
  const valRange = maxVal - minVal;
  const yMin = valRange === 0 ? minVal - 1 : minVal - valRange * 0.05;
  const yMax = valRange === 0 ? maxVal + 1 : maxVal + valRange * 0.05;

  const getX = (index: number) => {
    return margin.left + (index / (data.length - 1)) * chartWidth;
  };

  const getY = (val: number) => {
    if (yMax === yMin) return margin.top + chartHeight / 2;
    // SVG coordinates increase downwards, so invert y
    return margin.top + chartHeight - ((val - yMin) / (yMax - yMin)) * chartHeight;
  };

  // Generate paths
  const paths = keys.map((key) => {
    let pathD = "";
    let started = false;
    
    for (let i = 0; i < data.length; i++) {
      const val = data[i][key];
      if (val !== undefined && val !== null && !isNaN(val)) {
        const x = getX(i);
        const y = getY(val);
        if (!started) {
          pathD += `M ${x} ${y}`;
          started = true;
        } else {
          pathD += ` L ${x} ${y}`;
        }
      }
    }
    return pathD;
  });

  // Areas (optional, for first key, typically 'custom')
  const areaPath = (() => {
    if (keys.length === 0) return "";
    const key = keys[0];
    let pathD = "";
    let started = false;
    
    // Find first valid point to start
    let firstX = margin.left;
    let lastX = margin.left + chartWidth;
    
    for (let i = 0; i < data.length; i++) {
      const val = data[i][key];
      if (val !== undefined && val !== null && !isNaN(val)) {
        const x = getX(i);
        const y = getY(val);
        if (!started) {
          pathD += `M ${x} ${y}`;
          firstX = x;
          started = true;
        } else {
          pathD += ` L ${x} ${y}`;
        }
        lastX = x;
      }
    }
    
    if (started) {
      // Close the area path by drawing to the bottom of the chart
      const baselineY = margin.top + chartHeight;
      pathD += ` L ${lastX} ${baselineY} L ${firstX} ${baselineY} Z`;
    }
    return pathD;
  })();

  // Gridlines
  const yTicksCount = 5;
  const yGridVals = Array.from({ length: yTicksCount }, (_, i) => {
    return yMin + (i / (yTicksCount - 1)) * (yMax - yMin);
  });

  // Date labels along X-axis
  const xTicksCount = 6;
  const xIndices = Array.from({ length: xTicksCount }, (_, i) => {
    return Math.floor((i / (xTicksCount - 1)) * (data.length - 1));
  });

  // Handle interaction
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    if (!containerRef.current) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left - margin.left;
    
    if (mouseX < -10 || mouseX > chartWidth + 10) {
      setHoverIndex(null);
      setTooltipPos(null);
      return;
    }

    // Find closest index
    const pct = Math.max(0, Math.min(1, mouseX / chartWidth));
    const rawIndex = pct * (data.length - 1);
    const index = Math.round(rawIndex);
    
    if (index >= 0 && index < data.length) {
      setHoverIndex(index);
      
      // Calculate tooltip position (always inside the bounds)
      const x = getX(index);
      const isRightSide = x > width / 2;
      setTooltipPos({
        x: isRightSide ? x - 170 : x + 15,
        y: Math.min(e.clientY - rect.top + 10, height - 120),
      });
    }
  };

  const handleMouseLeave = () => {
    setHoverIndex(null);
    setTooltipPos(null);
  };

  const hoveredData = hoverIndex !== null ? data[hoverIndex] : null;

  return (
    <div ref={containerRef} className="chart-wrapper" style={{ height }}>
      <svg
        className="chart-svg"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", height: "100%" }}
      >
        {/* Y Gridlines and Labels */}
        {yGridVals.map((val, idx) => {
          const y = getY(val);
          return (
            <g key={`grid-y-${idx}`}>
              <line
                className="chart-grid-line"
                x1={margin.left}
                y1={y}
                x2={margin.left + chartWidth}
                y2={y}
              />
              <text
                className="chart-axis-text"
                x={margin.left - 8}
                y={y + 4}
                textAnchor="end"
              >
                {formatY(val)}
              </text>
            </g>
          );
        })}

        {/* X Gridlines and Labels */}
        {xIndices.map((idx, i) => {
          const x = getX(idx);
          const dateStr = data[idx]?.date || "";
          return (
            <g key={`grid-x-${i}`}>
              <text
                className="chart-axis-text"
                x={x}
                y={margin.top + chartHeight + 18}
                textAnchor="middle"
              >
                {dateStr}
              </text>
            </g>
          );
        })}

        {/* Main Y-axis & X-axis borders */}
        <line
          className="chart-axis-line"
          x1={margin.left}
          y1={margin.top}
          x2={margin.left}
          y2={margin.top + chartHeight}
        />
        <line
          className="chart-axis-line"
          x1={margin.left}
          y1={margin.top + chartHeight}
          x2={margin.left + chartWidth}
          y2={margin.top + chartHeight}
        />

        {/* Shaded Area for Custom portfolio if enabled */}
        {areaPath && keys.includes("custom") && (
          <path
            className="chart-area"
            d={areaPath}
            fill={colors["custom"] || "#3b82f6"}
          />
        )}

        {/* Line Paths */}
        {paths.map((d, idx) => {
          const key = keys[idx];
          return (
            <path
              key={`line-${key}`}
              className="chart-line"
              d={d}
              stroke={colors[key] || "#ccc"}
            />
          );
        })}

        {/* Hover elements */}
        {hoverIndex !== null && hoveredData && (
          <>
            {/* Vertical hover line */}
            <line
              stroke="#4b5563"
              strokeDasharray="2 2"
              strokeWidth="1.5"
              x1={getX(hoverIndex)}
              y1={margin.top}
              x2={getX(hoverIndex)}
              y2={margin.top + chartHeight}
            />

            {/* Intersection dots */}
            {keys.map((key) => {
              const val = hoveredData[key];
              if (val === undefined || val === null || isNaN(val)) return null;
              return (
                <circle
                  key={`dot-${key}`}
                  cx={getX(hoverIndex)}
                  cy={getY(val)}
                  r="4"
                  fill={colors[key] || "#fff"}
                  stroke={colors[key] ? "#111827" : "#000"}
                  strokeWidth="2"
                />
              );
            })}
          </>
        )}
      </svg>

      {/* Floating HTML Tooltip */}
      {hoverIndex !== null && tooltipPos && hoveredData && (
        <div
          className="chart-tooltip"
          style={{
            left: `${tooltipPos.x}px`,
            top: `${tooltipPos.y}px`,
          }}
        >
          <div className="chart-tooltip-date">{hoveredData.date}</div>
          {keys.map((key) => {
            const val = hoveredData[key];
            if (val === undefined || val === null || isNaN(val)) return null;
            return (
              <div key={`tooltip-${key}`} className="chart-tooltip-item">
                <span style={{ color: colors[key], fontWeight: 500 }}>{labels[key] || key}:</span>
                <span className="mono">{formatY(val)}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
