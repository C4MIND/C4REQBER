/**
 * Architecture Diagram Generator
 * Auto-generates C4/C4-TRIZ architecture diagrams from hypotheses
 */

import React, { useMemo } from 'react';
import { CanvasNode } from '../types';

interface ArchitectureDiagramProps {
  nodes: CanvasNode[];
  title?: string;
  width?: number;
  height?: number;
}

interface C4Component {
  id: string;
  name: string;
  type: 'system' | 'container' | 'component' | 'actor';
  description: string;
  c4State: string;
  trizPrinciples: number[];
  x: number;
  y: number;
}

interface C4Relation {
  from: string;
  to: string;
  type: string;
  description: string;
}

export const ArchitectureDiagram: React.FC<ArchitectureDiagramProps> = ({
  nodes,
  title = 'System Architecture',
  width = 800,
  height = 600,
}) => {
  const { components, relations } = useMemo(() => {
    const comps: C4Component[] = nodes.map((node, i) => ({
      id: node.id,
      name: node.label,
      type: node.data?.type || 'component',
      description: node.data?.description || '',
      c4State: node.c4State || '111',
      trizPrinciples: node.data?.trizPrinciples || [],
      x: 100 + (i % 3) * 250,
      y: 100 + Math.floor(i / 3) * 150,
    }));

    const rels: C4Relation[] = [];
    nodes.forEach((node, i) => {
      if (node.data?.connections) {
        node.data.connections.forEach((targetId: string) => {
          rels.push({
            from: node.id,
            to: targetId,
            type: 'uses',
            description: '',
          });
        });
      }
    });

    return { components: comps, relations: rels };
  }, [nodes]);

  const getColorByType = (type: string) => {
    const colors: Record<string, string> = {
      system: '#4A90E2',
      container: '#50C878',
      component: '#F5A623',
      actor: '#E94B3C',
    };
    return colors[type] || '#999';
  };

  const exportMermaid = () => {
    let mermaid = `C4Context\n  title ${title}\n\n`;
    
    components.forEach((comp) => {
      const type = comp.type === 'actor' ? 'Person' : 'System';
      mermaid += `  ${type}(${comp.id}, "${comp.name}", "${comp.description}")\n`;
    });
    
    mermaid += '\n';
    
    relations.forEach((rel) => {
      mermaid += `  Rel(${rel.from}, ${rel.to}, "${rel.description || 'uses'}")\n`;
    });
    
    return mermaid;
  };

  const exportPlantUML = () => {
    let uml = '@startuml\n!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml\n\n';
    uml += `title ${title}\n\n`;
    
    components.forEach((comp) => {
      if (comp.type === 'actor') {
        uml += `Person(${comp.id}, "${comp.name}", "${comp.description}")\n`;
      } else {
        uml += `System(${comp.id}, "${comp.name}", "${comp.description}")\n`;
      }
    });
    
    uml += '\n';
    
    relations.forEach((rel) => {
      uml += `Rel(${rel.from}, ${rel.to}, "${rel.description || 'uses'}")\n`;
    });
    
    uml += '\n@enduml';
    return uml;
  };

  return (
    <div className="architecture-diagram">
      <div className="diagram-header" style={{ marginBottom: 16 }}>
        <h3>{title}</h3>
        <div className="export-buttons">
          <button onClick={() => navigator.clipboard.writeText(exportMermaid())}>
            Copy Mermaid
          </button>
          <button onClick={() => navigator.clipboard.writeText(exportPlantUML())}>
            Copy PlantUML
          </button>
        </div>
      </div>
      
      <svg width={width} height={height} style={{ border: '1px solid #ddd' }}>
        {/* Relations */}
        {relations.map((rel, i) => {
          const from = components.find(c => c.id === rel.from);
          const to = components.find(c => c.id === rel.to);
          if (!from || !to) return null;
          
          return (
            <g key={`rel-${i}`}>
              <line
                x1={from.x + 60}
                y1={from.y + 30}
                x2={to.x + 60}
                y2={to.y + 30}
                stroke="#666"
                strokeWidth={2}
                markerEnd="url(#arrowhead)"
              />
            </g>
          );
        })}
        
        {/* Arrow marker */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth={10}
            markerHeight={7}
            refX={9}
            refY={3.5}
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
          </marker>
        </defs>
        
        {/* Components */}
        {components.map((comp) => (
          <g key={comp.id} transform={`translate(${comp.x}, ${comp.y})`}>
            <rect
              width={120}
              height={60}
              rx={8}
              fill={getColorByType(comp.type)}
              opacity={0.8}
            />
            <text
              x={60}
              y={25}
              textAnchor="middle"
              fill="white"
              fontSize={12}
              fontWeight="bold"
            >
              {comp.name}
            </text>
            <text
              x={60}
              y={45}
              textAnchor="middle"
              fill="white"
              fontSize={10}
            >
              C4: {comp.c4State}
            </text>
            
            {/* TRIZ principles */}
            {comp.trizPrinciples.length > 0 && (
              <g transform="translate(125, 0)">
                {comp.trizPrinciples.slice(0, 3).map((p, i) => (
                  <circle
                    key={i}
                    cx={0}
                    cy={i * 15 + 8}
                    r={6}
                    fill="#E94B3C"
                  />
                ))}
              </g>
            )}
          </g>
        ))}
      </svg>
      
      <div className="diagram-legend" style={{ marginTop: 16, fontSize: 12 }}>
        <div><span style={{ color: '#4A90E2' }}>■</span> System</div>
        <div><span style={{ color: '#50C878' }}>■</span> Container</div>
        <div><span style={{ color: '#F5A623' }}>■</span> Component</div>
        <div><span style={{ color: '#E94B3C' }}>■</span> Actor</div>
      </div>
    </div>
  );
};

export default ArchitectureDiagram;
