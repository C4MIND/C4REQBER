/**
 * Small Multiples Component
 * Compare multiple simulation runs side-by-side
 */

import React, { useMemo } from 'react';

export interface SimulationRun {
  id: string;
  label: string;
  color: string;
  timeSeries: { t: number; v: number }[];
  metrics: Record<string, number>;
}

interface SmallMultiplesProps {
  runs: SimulationRun[];
  width?: number;
  height?: number;
  metricName?: string;
}

export const SmallMultiples: React.FC<SmallMultiplesProps> = ({
  runs,
  width = 1200,
  height = 300,
  metricName = 'value',
}) => {
  const cols = Math.min(runs.length, 4);
  const rows = Math.ceil(runs.length / cols);
  
  const cellWidth = (width - 40) / cols;
  const cellHeight = (height - 40) / rows;
  
  const globalDomain = useMemo(() => {
    let minT = Infinity, maxT = -Infinity;
    let minV = Infinity, maxV = -Infinity;
    
    runs.forEach(run => {
      run.timeSeries.forEach(p => {
        minT = Math.min(minT, p.t);
        maxT = Math.max(maxT, p.t);
        minV = Math.min(minV, p.v);
        maxV = Math.max(maxV, p.v);
      });
    });
    
    return { t: [minT, maxT] as [number, number], v: [minV, maxV] as [number, number] };
  }, [runs]);
  
  const scaleX = (t: number) => {
    const [min, max] = globalDomain.t;
    return ((t - min) / (max - min)) * (cellWidth - 40) + 30;
  };
  
  const scaleY = (v: number) => {
    const [min, max] = globalDomain.v;
    return cellHeight - 30 - ((v - min) / (max - min)) * (cellHeight - 50);
  };
  
  const generatePath = (series: { t: number; v: number }[]) => {
    if (series.length === 0) return '';
    
    return series
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(p.t)} ${scaleY(p.v)}`)
      .join(' ');
  };
  
  return (
    <div className="small-multiples" style={{ width, height }}>
      <svg width={width} height={height}>
        {/* Grid background */}
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f0f0f0" strokeWidth={1}/>
          </pattern>
        </defs>
        
        {runs.map((run, i) => {
          const col = i % cols;
          const row = Math.floor(i / cols);
          const x = col * cellWidth + 20;
          const y = row * cellHeight + 20;
          
          return (
            <g key={run.id} transform={`translate(${x}, ${y})`}>
              {/* Cell background */}
              <rect
                width={cellWidth - 10}
                height={cellHeight - 10}
                fill="url(#grid)"
                stroke="#ddd"
                strokeWidth={1}
              />
              
              {/* Title */}
              <text x={10} y={20} fontSize={12} fontWeight="bold">
                {run.label}
              </text>
              
              {/* Chart area */}
              <g transform="translate(0, 30)">
                {/* Y axis */}
                <line x1={30} y1={10} x2={30} y2={cellHeight - 50} stroke="#666" />
                
                {/* X axis */}
                <line x1={30} y1={cellHeight - 50} x2={cellWidth - 20} y2={cellHeight - 50} stroke="#666" />
                
                {/* Data line */}
                <path
                  d={generatePath(run.timeSeries)}
                  fill="none"
                  stroke={run.color}
                  strokeWidth={2}
                />
                
                {/* Area under curve */}
                {run.timeSeries.length > 0 && (
                  <path
                    d={`${generatePath(run.timeSeries)} L ${scaleX(run.timeSeries[run.timeSeries.length - 1].t)} ${cellHeight - 50} L ${scaleX(run.timeSeries[0].t)} ${cellHeight - 50} Z`}
                    fill={run.color}
                    opacity={0.2}
                  />
                )}
              </g>
              
              {/* Key metrics */}
              <g transform={`translate(${cellWidth - 100}, 20)`}>
                {Object.entries(run.metrics).slice(0, 3).map(([k, v], j) => (
                  <text key={k} y={j * 15} fontSize={10} fill="#666">
                    {k}: {typeof v === 'number' ? v.toFixed(2) : v}
                  </text>
                ))}
              </g>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default SmallMultiples;
