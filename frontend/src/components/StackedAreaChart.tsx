import React, { useState, useRef, useEffect } from "react";

interface DriftPoint {
  date: string;
  [ticker: string]: any; // Ticker weight percentages (0-100)
}

interface StackedAreaChartProps {
  data: DriftPoint[];
  tickers: string[];
  colors: { [ticker: string]: string };
  height?: number;
}

export const StackedAreaChart: React.FC<StackedAreaChartProps> = ({
  data,
  tickers,
  colors,
  height = 360,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);

  useEffect(() => {
    if (!containerRef.current) return;
    const handleResize = () => {
      setWidth(containerRef.current?.getBoundingClientRect().width || 800);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  if (!data || data.length === 0 || !tickers || tickers.length === 0) {
    return (
      <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center", color: "#6b7280" }}>
        No data available for weight drift.
      </div>
    );
  }

  const margin = { top: 20, right: 30, bottom: 40, left: 55 };
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;

  const getX = (index: number) => {
    return margin.left + (index / (data.length - 1)) * chartWidth;
  };

  const getY = (val: number) => {
    // val is 0 to 100 %
    return margin.top + chartHeight - (val / 100) * chartHeight;
  };

  // Generate stacked values
  // stackValues[i] contains cumulative weights for data[i]:
  // e.g. for tickers [A, B, C] -> { A: weightA, B: weightA+weightB, C: 100 }
  const stackValues = data.map((d) => {
    const accum: { [ticker: string]: number } = {};
    let sum = 0;
    tickers.forEach((t) => {
      sum += d[t] || 0;
      accum[t] = sum;
    });
    return accum;
  });

  // Generate path for each ticker layer
  // To draw a layer: we draw from left to right along the top boundary,
  // then right to left along the bottom boundary (which is the top boundary of the previous layer),
  // then close.
  const layers = tickers.map((ticker, tickerIdx) => {
    let topPoints = "";
    let bottomPoints = "";

    for (let i = 0; i < data.length; i++) {
      const topVal = stackValues[i][ticker];
      const bottomVal = tickerIdx === 0 ? 0 : stackValues[i][tickers[tickerIdx - 1]];

      const x = getX(i);
      const topY = getY(topVal);
      const bottomY = getY(bottomVal);

      if (i === 0) {
        topPoints += `M ${x} ${topY}`;
        bottomPoints += ` L ${x} ${bottomY}`;
      } else {
        topPoints += ` L ${x} ${topY}`;
        // Prepend bottom points to draw backwards later
        bottomPoints = ` L ${x} ${bottomY}` + bottomPoints;
      }
    }

    return topPoints + bottomPoints + " Z";
  });

  // Handle hover
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    if (!containerRef.current) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left - margin.left;

    if (mouseX < -10 || mouseX > chartWidth + 10) {
      setHoverIndex(null);
      setTooltipPos(null);
      return;
    }

    const pct = Math.max(0, Math.min(1, mouseX / chartWidth));
    const index = Math.round(pct * (data.length - 1));

    if (index >= 0 && index < data.length) {
      setHoverIndex(index);
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
        {/* Y Gridlines and Labels (0%, 25%, 50%, 75%, 100%) */}
        {[0, 25, 50, 75, 100].map((val) => {
          const y = getY(val);
          return (
            <g key={`grid-y-${val}`}>
              <line className="chart-grid-line" x1={margin.left} y1={y} x2={margin.left + chartWidth} y2={y} />
              <text className="chart-axis-text" x={margin.left - 8} y={y + 4} textAnchor="end">
                {val}%
              </text>
            </g>
          );
        })}

        {/* X Labels */}
        {[0, 0.2, 0.4, 0.6, 0.8, 1].map((pct, idx) => {
          const dataIdx = Math.floor(pct * (data.length - 1));
          const x = getX(dataIdx);
          const dateStr = data[dataIdx]?.date || "";
          return (
            <g key={`grid-x-${idx}`}>
              <text className="chart-axis-text" x={x} y={margin.top + chartHeight + 18} textAnchor="middle">
                {dateStr}
              </text>
            </g>
          );
        })}

        {/* Layer Polygons */}
        {layers.map((dPath, idx) => {
          const ticker = tickers[idx];
          return (
            <path
              key={`layer-${ticker}`}
              d={dPath}
              fill={colors[ticker] || "#ccc"}
              opacity="0.8"
              stroke="#111827"
              strokeWidth="0.5"
            />
          );
        })}

        {/* Vertical Hover Line */}
        {hoverIndex !== null && (
          <line
            stroke="#ffffff"
            strokeDasharray="2 2"
            strokeWidth="1.5"
            x1={getX(hoverIndex)}
            y1={margin.top}
            x2={getX(hoverIndex)}
            y2={margin.top + chartHeight}
          />
        )}
      </svg>

      {/* Hover Tooltip */}
      {hoverIndex !== null && tooltipPos && hoveredData && (
        <div
          className="chart-tooltip"
          style={{
            left: `${tooltipPos.x}px`,
            top: `${tooltipPos.y}px`,
          }}
        >
          <div className="chart-tooltip-date">{hoveredData.date}</div>
          {tickers.map((t) => {
            const val = hoveredData[t];
            return (
              <div key={`tooltip-${t}`} className="chart-tooltip-item">
                <span style={{ color: colors[t], fontWeight: 500 }}>{t}:</span>
                <span className="mono">{val !== undefined ? `${val.toFixed(2)}%` : "0.00%"}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
