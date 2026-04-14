import React, { useRef, useState, useCallback, useEffect } from 'react'
import type { Point, Viewport, CanvasNode, CanvasEdge, CanvasEvent } from '../types'

interface CanvasProps {
  width: number
  height: number
  nodes: CanvasNode[]
  edges: CanvasEdge[]
  viewport?: Viewport
  onEvent?: (event: CanvasEvent) => void
  children?: React.ReactNode
}

export const Canvas: React.FC<CanvasProps> = ({
  width,
  height,
  nodes,
  edges,
  viewport: initialViewport = { x: 0, y: 0, zoom: 1 },
  onEvent,
  children
}) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const [viewport, setViewport] = useState<Viewport>(initialViewport)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState<Point | null>(null)

  // Transform point from screen to world coordinates
  const screenToWorld = useCallback((screenPoint: Point): Point => {
    return {
      x: screenPoint.x / viewport.zoom + viewport.x,
      y: screenPoint.y / viewport.zoom + viewport.y
    }
  }, [viewport])

  // Handle mouse events for panning
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.target === svgRef.current) {
      setIsDragging(true)
      setDragStart({ x: e.clientX, y: e.clientY })
    }
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging && dragStart) {
      const dx = (e.clientX - dragStart.x) / viewport.zoom
      const dy = (e.clientY - dragStart.y) / viewport.zoom
      
      setViewport(prev => ({
        ...prev,
        x: prev.x - dx,
        y: prev.y - dy
      }))
      
      setDragStart({ x: e.clientX, y: e.clientY })
    }
  }, [isDragging, dragStart, viewport.zoom])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
    setDragStart(null)
  }, [])

  // Handle zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
    const newZoom = Math.max(0.1, Math.min(5, viewport.zoom * zoomFactor))
    
    // Zoom towards mouse position
    const rect = svgRef.current?.getBoundingClientRect()
    if (rect) {
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top
      
      const worldX = mouseX / viewport.zoom + viewport.x
      const worldY = mouseY / viewport.zoom + viewport.y
      
      setViewport({
        x: worldX - mouseX / newZoom,
        y: worldY - mouseY / newZoom,
        zoom: newZoom
      })
    }
  }, [viewport])

  // Handle node click
  const handleNodeClick = useCallback((nodeId: string) => {
    onEvent?.({
      type: 'node-click',
      target: nodeId
    })
  }, [onEvent])

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{
        background: '#0f0f1a',
        cursor: isDragging ? 'grabbing' : 'grab',
        userSelect: 'none'
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
    >
      {/* Grid background */}
      <defs>
        <pattern
          id="grid"
          width="50"
          height="50"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M 50 0 L 0 0 0 50"
            fill="none"
            stroke="#1a1a2e"
            strokeWidth="1"
          />
        </pattern>
      </defs>
      
      <rect width="100%" height="100%" fill="url(#grid)" />

      {/* Main transform group */}
      <g transform={`translate(${-viewport.x * viewport.zoom}, ${-viewport.y * viewport.zoom}) scale(${viewport.zoom})`}>
        {/* Render edges */}
        {edges.map(edge => (
          <CanvasEdge
            key={edge.id}
            edge={edge}
            nodes={nodes}
          />
        ))}

        {/* Render nodes */}
        {nodes.map(node => (
          <CanvasNode
            key={node.id}
            node={node}
            onClick={() => handleNodeClick(node.id)}
          />
        ))}

        {/* Children (custom overlays) */}
        {children}
      </g>

      {/* UI Overlay (fixed position) */}
      <g transform={`translate(10, 10)`}>
        <rect x="0" y="0" width="150" height="60" fill="#1a1a2e" rx="5" />
        <text x="10" y="20" fill="#4ECDC4" fontSize="12" fontFamily="monospace">
          ZOOM: {(viewport.zoom * 100).toFixed(0)}%
        </text>
        <text x="10" y="40" fill="#6c757d" fontSize="10" fontFamily="monospace">
          DRAG TO PAN • SCROLL TO ZOOM
        </text>
      </g>
    </svg>
  )
}

// Sub-component for rendering edges
const CanvasEdge: React.FC<{ edge: CanvasEdge; nodes: CanvasNode[] }> = ({ edge, nodes }) => {
  const sourceNode = nodes.find(n => n.id === edge.source)
  const targetNode = nodes.find(n => n.id === edge.target)
  
  if (!sourceNode || !targetNode) return null

  const x1 = sourceNode.position.x + sourceNode.size.width / 2
  const y1 = sourceNode.position.y + sourceNode.size.height / 2
  const x2 = targetNode.position.x + targetNode.size.width / 2
  const y2 = targetNode.position.y + targetNode.size.height / 2

  const color = edge.type === 'c4-transition' ? '#4ECDC4' : 
                edge.type === 'evolution' ? '#9b59b6' : '#6c757d'

  return (
    <g>
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={color}
        strokeWidth={edge.type === 'c4-transition' ? 3 : 2}
        opacity={0.6}
      />
      {edge.label && (
        <text
          x={(x1 + x2) / 2}
          y={(y1 + y2) / 2 - 5}
          fill="#ffffff"
          fontSize="10"
          textAnchor="middle"
          style={{ pointerEvents: 'none' }}
        >
          {edge.label}
        </text>
      )}
    </g>
  )
}

// Sub-component for rendering nodes
const CanvasNode: React.FC<{ node: CanvasNode; onClick: () => void }> = ({ node, onClick }) => {
  const fillColor = node.selected ? '#4ECDC4' : 
                    node.highlighted ? '#FFE66D' : '#1a1a2e'
  const strokeColor = node.selected ? '#FFE66D' : '#4ECDC4'

  return (
    <g
      transform={`translate(${node.position.x}, ${node.position.y})`}
      onClick={onClick}
      style={{ cursor: 'pointer' }}
    >
      <rect
        width={node.size.width}
        height={node.size.height}
        fill={fillColor}
        stroke={strokeColor}
        strokeWidth={node.selected ? 3 : 2}
        rx={5}
      />
      <text
        x={node.size.width / 2}
        y={node.size.height / 2}
        fill={node.selected ? '#0f0f1a' : '#ffffff'}
        fontSize="12"
        fontWeight="bold"
        textAnchor="middle"
        dominantBaseline="middle"
        style={{ pointerEvents: 'none' }}
      >
        {node.id}
      </text>
    </g>
  )
}

export default Canvas
