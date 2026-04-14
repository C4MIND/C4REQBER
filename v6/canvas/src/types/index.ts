// TURBO-CDI v6.0 Canvas Types
// Type definitions for visual canvas components

export interface Point {
  x: number
  y: number
}

export interface Size {
  width: number
  height: number
}

export interface Bounds {
  minX: number
  minY: number
  maxX: number
  maxY: number
}

// C4 State representation
export interface C4State {
  code: string
  time: 0 | 1 | 2  // Past=0, Present=1, Future=2
  scale: 0 | 1 | 2 // Concrete=0, Abstract=1, Meta=2
  agency: 0 | 1 | 2 // Self=0, Other=1, System=2
  label: string
  description: string
}

// Position in 3D space (for isometric projection)
export interface Position3D {
  x: number
  y: number
  z: number
}

// Node in the canvas
export interface CanvasNode {
  id: string
  type: 'c4-state' | 'hypothesis' | 'simulation' | 'diagram'
  position: Point
  size: Size
  data: any
  selected?: boolean
  highlighted?: boolean
}

// Edge connecting nodes
export interface CanvasEdge {
  id: string
  source: string
  target: string
  type: 'c4-transition' | 'dependency' | 'flow' | 'evolution'
  label?: string
  animated?: boolean
}

// Viewport state
export interface Viewport {
  x: number
  y: number
  zoom: number
}

// Simulation result for visualization
export interface SimulationResult {
  id: string
  hypothesisId: string
  timestamp: number
  parameters: Record<string, number>
  metrics: Record<string, number>
  confidence: number
  status: 'running' | 'complete' | 'error'
}

// Canvas event types
export interface CanvasEvent {
  type: 'node-click' | 'node-hover' | 'edge-click' | 'canvas-click' | 'zoom' | 'pan'
  target?: string
  position?: Point
  viewport?: Viewport
}

// C4 Grid configuration
export interface C4GridConfig {
  cellSize: number
  spacing: number
  isometric: boolean
  showLabels: boolean
  highlightTransitions: boolean
}

// Diagram export options
export interface ExportOptions {
  format: 'svg' | 'png' | 'pdf'
  scale?: number
  background?: string
  includeMetadata?: boolean
}

// Animation configuration
export interface AnimationConfig {
  duration: number
  easing: 'linear' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'bounce'
  delay?: number
}

// Pattern for meta-simulation
export interface SimulationPattern {
  id: string
  name: string
  category: 'physics' | 'stochastic' | 'agent' | 'circuit' | 'economic' | 'biological'
  icon: string
  description: string
  parameters: PatternParameter[]
}

export interface PatternParameter {
  name: string
  type: 'number' | 'string' | 'boolean' | 'select'
  default: any
  min?: number
  max?: number
  options?: string[]
  description: string
}
