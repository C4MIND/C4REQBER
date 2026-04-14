// SVG Utilities for Canvas
// Helper functions for SVG manipulation and calculations

import type { Point, Position3D, Bounds, Size } from '../types'

// Isometric projection constants
const ISO_ANGLE = 30 * (Math.PI / 180) // 30 degrees
const ISO_COS = Math.cos(ISO_ANGLE)
const ISO_SIN = Math.sin(ISO_ANGLE)

/**
 * Project 3D coordinates to 2D isometric view
 */
export function projectIsometric(pos: Position3D, center: Point): Point {
  return {
    x: center.x + (pos.x - pos.z) * ISO_COS,
    y: center.y + (pos.x + pos.z) * ISO_SIN - pos.y
  }
}

/**
 * Convert C4 state code (000-222) to 3D position
 */
export function c4ToPosition(code: string): Position3D {
  if (code.length !== 3) return { x: 0, y: 0, z: 0 }
  
  const time = parseInt(code[0])    // 0, 1, 2
  const scale = parseInt(code[1])   // 0, 1, 2
  const agency = parseInt(code[2])  // 0, 1, 2
  
  return {
    x: (agency - 1) * 100,  // -100, 0, 100
    y: (scale - 1) * 100,   // -100, 0, 100
    z: (time - 1) * 100     // -100, 0, 100
  }
}

/**
 * Get color for C4 time dimension
 */
export function getC4TimeColor(time: number): string {
  const colors = ['#3498db', '#2ecc71', '#9b59b6'] // Past=blue, Present=green, Future=purple
  return colors[time] || '#6c757d'
}

/**
 * Calculate distance between two points
 */
export function distance(a: Point, b: Point): number {
  return Math.sqrt(Math.pow(b.x - a.x, 2) + Math.pow(b.y - a.y, 2))
}

/**
 * Check if point is inside bounds
 */
export function isInBounds(point: Point, bounds: Bounds): boolean {
  return point.x >= bounds.minX && point.x <= bounds.maxX &&
         point.y >= bounds.minY && point.y <= bounds.maxY
}

/**
 * Transform point with viewport (zoom + pan)
 */
export function transformPoint(point: Point, viewport: { x: number; y: number; zoom: number }): Point {
  return {
    x: (point.x - viewport.x) * viewport.zoom,
    y: (point.y - viewport.y) * viewport.zoom
  }
}

/**
 * Inverse transform (screen to world coordinates)
 */
export function inverseTransformPoint(point: Point, viewport: { x: number; y: number; zoom: number }): Point {
  return {
    x: point.x / viewport.zoom + viewport.x,
    y: point.y / viewport.zoom + viewport.y
  }
}

/**
 * Generate unique ID
 */
export function generateId(prefix: string = ''): string {
  return `${prefix}${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Calculate bounds for a set of points
 */
export function calculateBounds(points: Point[]): Bounds {
  if (points.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0 }
  }
  
  return points.reduce((bounds, point) => ({
    minX: Math.min(bounds.minX, point.x),
    minY: Math.min(bounds.minY, point.y),
    maxX: Math.max(bounds.maxX, point.x),
    maxY: Math.max(bounds.maxY, point.y)
  }), {
    minX: points[0].x,
    minY: points[0].y,
    maxX: points[0].x,
    maxY: points[0].y
  })
}

/**
 * Create SVG path from points
 */
export function createPath(points: Point[], closed: boolean = false): string {
  if (points.length === 0) return ''
  
  const commands = points.map((p, i) => 
    i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`
  )
  
  if (closed) commands.push('Z')
  
  return commands.join(' ')
}

/**
 * Create smooth bezier curve through points
 */
export function createSmoothPath(points: Point[]): string {
  if (points.length < 2) return createPath(points)
  
  // Simple smoothing using quadratic bezier
  const commands: string[] = [`M ${points[0].x} ${points[0].y}`]
  
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1]
    const curr = points[i]
    const midX = (prev.x + curr.x) / 2
    const midY = (prev.y + curr.y) / 2
    
    commands.push(`Q ${prev.x} ${prev.y}, ${midX} ${midY}`)
  }
  
  const last = points[points.length - 1]
  commands.push(`L ${last.x} ${last.y}`)
  
  return commands.join(' ')
}

/**
 * Format number for display
 */
export function formatNumber(num: number, decimals: number = 2): string {
  if (Math.abs(num) >= 1000000) return (num / 1000000).toFixed(decimals) + 'M'
  if (Math.abs(num) >= 1000) return (num / 1000).toFixed(decimals) + 'k'
  return num.toFixed(decimals)
}

/**
 * Generate color from string (consistent hashing)
 */
export function stringToColor(str: string): string {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  const hue = Math.abs(hash % 360)
  return `hsl(${hue}, 70%, 60%)`
}

/**
 * Easing functions for animations
 */
export const easing = {
  linear: (t: number) => t,
  'ease-in': (t: number) => t * t,
  'ease-out': (t: number) => 1 - (1 - t) * (1 - t),
  'ease-in-out': (t: number) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2,
  bounce: (t: number) => {
    const n1 = 7.5625
    const d1 = 2.75
    if (t < 1 / d1) return n1 * t * t
    if (t < 2 / d1) return n1 * (t -= 1.5 / d1) * t + 0.75
    if (t < 2.5 / d1) return n1 * (t -= 2.25 / d1) * t + 0.9375
    return n1 * (t -= 2.625 / d1) * t + 0.984375
  }
}
