import React, { useMemo, useState, useCallback } from 'react'
import { Canvas } from './Canvas'
import type { CanvasNode, CanvasEdge, C4State, Viewport } from '../types'
import { projectIsometric, c4ToPosition, getC4TimeColor, generateId } from '../utils/svg'

interface C4VisualMapProps {
  width?: number
  height?: number
  selectedState?: string
  onStateSelect?: (state: C4State) => void
  showTransitions?: boolean
}

// All 27 C4 states
const C4_STATES: C4State[] = [
  // Time = 0 (Past)
  { code: '000', time: 0, scale: 0, agency: 0, label: 'Past Concrete Self', description: 'Personal concrete memories' },
  { code: '001', time: 0, scale: 0, agency: 1, label: 'Past Concrete Other', description: 'Others concrete experiences' },
  { code: '002', time: 0, scale: 0, agency: 2, label: 'Past Concrete System', description: 'Historical concrete events' },
  { code: '010', time: 0, scale: 1, agency: 0, label: 'Past Abstract Self', description: 'Personal learned patterns' },
  { code: '011', time: 0, scale: 1, agency: 1, label: 'Past Abstract Other', description: 'Shared abstract experiences' },
  { code: '012', time: 0, scale: 1, agency: 2, label: 'Past Abstract System', description: 'Historical patterns' },
  { code: '020', time: 0, scale: 2, agency: 0, label: 'Past Meta Self', description: 'Personal meta-cognition' },
  { code: '021', time: 0, scale: 2, agency: 1, label: 'Past Meta Other', description: 'Meta-level observations' },
  { code: '022', time: 0, scale: 2, agency: 2, label: 'Past Meta System', description: 'System meta-patterns' },
  
  // Time = 1 (Present)
  { code: '100', time: 1, scale: 0, agency: 0, label: 'Present Concrete Self', description: 'Current personal state' },
  { code: '101', time: 1, scale: 0, agency: 1, label: 'Present Concrete Other', description: 'Observing others now' },
  { code: '102', time: 1, scale: 0, agency: 2, label: 'Present Concrete System', description: 'Current system state' },
  { code: '110', time: 1, scale: 1, agency: 0, label: 'Present Abstract Self', description: 'Abstracting experience' },
  { code: '111', time: 1, scale: 1, agency: 1, label: 'Present Abstract Other', description: 'Collaborative abstraction' },
  { code: '112', time: 1, scale: 1, agency: 2, label: 'Present Abstract System', description: 'System-level patterns' },
  { code: '120', time: 1, scale: 2, agency: 0, label: 'Present Meta Self', description: 'Present meta-awareness' },
  { code: '121', time: 1, scale: 2, agency: 1, label: 'Present Meta Other', description: 'Meta collaboration' },
  { code: '122', time: 1, scale: 2, agency: 2, label: 'Present Meta System', description: 'System meta-cognition' },
  
  // Time = 2 (Future)
  { code: '200', time: 2, scale: 0, agency: 0, label: 'Future Concrete Self', description: 'Personal concrete goals' },
  { code: '201', time: 2, scale: 0, agency: 1, label: 'Future Concrete Other', description: 'Others future actions' },
  { code: '202', time: 2, scale: 0, agency: 2, label: 'Future Concrete System', description: 'Concrete predictions' },
  { code: '210', time: 2, scale: 1, agency: 0, label: 'Future Abstract Self', description: 'Abstract planning' },
  { code: '211', time: 2, scale: 1, agency: 1, label: 'Future Abstract Other', description: 'Collaborative planning' },
  { code: '212', time: 2, scale: 1, agency: 2, label: 'Future Abstract System', description: 'System predictions' },
  { code: '220', time: 2, scale: 2, agency: 0, label: 'Future Meta Self', description: 'Meta-level vision' },
  { code: '221', time: 2, scale: 2, agency: 1, label: 'Future Meta Other', description: 'Meta collaboration future' },
  { code: '222', time: 2, scale: 2, agency: 2, label: 'Future Meta System', description: 'System meta-vision' },
]

export const C4VisualMap: React.FC<C4VisualMapProps> = ({
  width = 800,
  height = 600,
  selectedState = '111',
  onStateSelect,
  showTransitions = true
}) => {
  const [hoveredState, setHoveredState] = useState<string | null>(null)

  // Calculate node positions using isometric projection
  const nodes = useMemo((): CanvasNode[] => {
    const center = { x: width / 2, y: height / 2 + 100 }
    const cellSize = 60
    
    return C4_STATES.map((state, index) => {
      // Calculate 3D position
      const pos3D = c4ToPosition(state.code)
      
      // Apply isometric projection
      const pos = projectIsometric(
        { 
          x: pos3D.x * 0.8, 
          y: pos3D.y * 0.5, 
          z: pos3D.z * 0.8 
        },
        center
      )
      
      const isSelected = state.code === selectedState
      const isHovered = state.code === hoveredState
      
      return {
        id: state.code,
        type: 'c4-state',
        position: { 
          x: pos.x - cellSize / 2, 
          y: pos.y - cellSize / 2 
        },
        size: { width: cellSize, height: cellSize },
        data: state,
        selected: isSelected,
        highlighted: isHovered
      }
    })
  }, [width, height, selectedState, hoveredState])

  // Generate transition edges
  const edges = useMemo((): CanvasEdge[] => {
    if (!showTransitions) return []
    
    const transitions: CanvasEdge[] = []
    
    // Connect adjacent states (differ by 1 in one dimension)
    C4_STATES.forEach((state, i) => {
      C4_STATES.forEach((other, j) => {
        if (i >= j) return
        
        const t1 = parseInt(state.code[0])
        const t2 = parseInt(other.code[0])
        const s1 = parseInt(state.code[1])
        const s2 = parseInt(other.code[1])
        const a1 = parseInt(state.code[2])
        const a2 = parseInt(other.code[2])
        
        // Check if differ by exactly 1 in one dimension
        const diff = Math.abs(t1 - t2) + Math.abs(s1 - s2) + Math.abs(a1 - a2)
        
        if (diff === 1) {
          transitions.push({
            id: generateId('edge-'),
            source: state.code,
            target: other.code,
            type: 'c4-transition',
            animated: true
          })
        }
      })
    })
    
    return transitions
  }, [showTransitions])

  // Handle node click
  const handleNodeClick = useCallback((nodeId: string) => {
    const state = C4_STATES.find(s => s.code === nodeId)
    if (state) {
      onStateSelect?.(state)
    }
  }, [onStateSelect])

  // Custom render for C4 nodes (isometric cubes)
  const renderC4Node = (node: CanvasNode) => {
    const state = node.data as C4State
    const timeColor = getC4TimeColor(state.time)
    const isSelected = node.selected
    
    // Draw isometric cube
    const size = node.size.width
    const h = size * 0.5 // half height for isometric
    
    // Top face
    const topPoints = [
      { x: size / 2, y: 0 },
      { x: size, y: h / 2 },
      { x: size / 2, y: h },
      { x: 0, y: h / 2 }
    ]
    
    // Right face
    const rightPoints = [
      { x: size, y: h / 2 },
      { x: size, y: size - h / 2 },
      { x: size / 2, y: size },
      { x: size / 2, y: h }
    ]
    
    // Left face
    const leftPoints = [
      { x: 0, y: h / 2 },
      { x: size / 2, y: h },
      { x: size / 2, y: size },
      { x: 0, y: size - h / 2 }
    ]
    
    const pathData = (points: typeof topPoints) => 
      `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y} L ${points[2].x} ${points[2].y} L ${points[3].x} ${points[3].y} Z`

    return (
      <g
        key={node.id}
        transform={`translate(${node.position.x}, ${node.position.y})`}
        onClick={() => handleNodeClick(node.id)}
        onMouseEnter={() => setHoveredState(node.id)}
        onMouseLeave={() => setHoveredState(null)}
        style={{ cursor: 'pointer' }}
      >
        {/* Right face */}
        <path
          d={pathData(rightPoints)}
          fill={timeColor}
          opacity={0.7}
          stroke={isSelected ? '#FFE66D' : 'none'}
          strokeWidth={2}
        />
        
        {/* Left face */}
        <path
          d={pathData(leftPoints)}
          fill={timeColor}
          opacity={0.5}
          stroke={isSelected ? '#FFE66D' : 'none'}
          strokeWidth={2}
        />
        
        {/* Top face */}
        <path
          d={pathData(topPoints)}
          fill={timeColor}
          opacity={isSelected ? 1 : 0.9}
          stroke={isSelected ? '#FFE66D' : '#ffffff'}
          strokeWidth={isSelected ? 3 : 1}
        />
        
        {/* Label */}
        <text
          x={size / 2}
          y={h / 2 + 5}
          fill="#0f0f1a"
          fontSize="11"
          fontWeight="bold"
          textAnchor="middle"
          style={{ pointerEvents: 'none' }}
        >
          {node.id}
        </text>
        
        {/* Hover tooltip */}
        {node.highlighted && (
          <g transform={`translate(0, -40)`}>
            <rect
              x={-10}
              y={0}
              width={size + 20}
              height={35}
              fill="#1a1a2e"
              stroke="#4ECDC4"
              strokeWidth={1}
              rx={3}
            />
            <text
              x={size / 2}
              y={15}
              fill="#ffffff"
              fontSize="9"
              textAnchor="middle"
            >
              {state.label}
            </text>
            <text
              x={size / 2}
              y={28}
              fill="#6c757d"
              fontSize="8"
              textAnchor="middle"
            >
              {state.description}
            </text>
          </g>
        )}
      </g>
    )
  }

  return (
    <div style={{ position: 'relative' }}>
      <Canvas
        width={width}
        height={height}
        nodes={nodes}
        edges={edges}
        viewport={{ x: 0, y: 0, zoom: 1 }}
        onEvent={(e) => {
          if (e.type === 'node-click' && e.target) {
            handleNodeClick(e.target)
          }
        }}
      >
        {/* Custom render overlay */}
        {nodes.map(renderC4Node)}
      </Canvas>
      
      {/* Legend */}
      <div
        style={{
          position: 'absolute',
          top: 10,
          right: 10,
          background: '#1a1a2e',
          padding: '10px',
          borderRadius: '5px',
          border: '1px solid #4ECDC4',
          color: '#ffffff',
          fontSize: '12px',
          fontFamily: 'monospace'
        }}
      >
        <div style={{ marginBottom: '5px', fontWeight: 'bold', color: '#4ECDC4' }}>
          C4 STATE SPACE
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '3px' }}>
          <div style={{ width: 12, height: 12, background: '#3498db' }}></div>
          <span>Past (Time=0)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '3px' }}>
          <div style={{ width: 12, height: 12, background: '#2ecc71' }}></div>
          <span>Present (Time=1)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: 12, height: 12, background: '#9b59b6' }}></div>
          <span>Future (Time=2)</span>
        </div>
        <div style={{ marginTop: '10px', fontSize: '10px', color: '#6c757d' }}>
          Click state to select
          <br />
          Drag to pan, scroll to zoom
        </div>
      </div>
      
      {/* Selected state info */}
      {selectedState && (
        <div
          style={{
            position: 'absolute',
            bottom: 10,
            left: 10,
            background: '#1a1a2e',
            padding: '15px',
            borderRadius: '5px',
            border: '2px solid #FFE66D',
            color: '#ffffff',
            fontSize: '13px',
            fontFamily: 'monospace',
            minWidth: '250px'
          }}
        >
          <div style={{ color: '#FFE66D', fontWeight: 'bold', marginBottom: '8px' }}>
            SELECTED: {selectedState}
          </div>
          {(() => {
            const state = C4_STATES.find(s => s.code === selectedState)
            if (!state) return null
            return (
              <>
                <div style={{ marginBottom: '5px' }}>{state.label}</div>
                <div style={{ color: '#6c757d', fontSize: '11px', marginBottom: '5px' }}>
                  {state.description}
                </div>
                <div style={{ fontSize: '11px' }}>
                  <span style={{ color: getC4TimeColor(state.time) }}>
                    ● {['Past', 'Present', 'Future'][state.time]}
                  </span>
                  {' × '}
                  <span style={{ color: '#4ECDC4' }}>
                    {['Concrete', 'Abstract', 'Meta'][state.scale]}
                  </span>
                  {' × '}
                  <span style={{ color: '#FF6B6B' }}>
                    {['Self', 'Other', 'System'][state.agency]}
                  </span>
                </div>
              </>
            )
          })()}
        </div>
      )}
    </div>
  )
}

export default C4VisualMap
