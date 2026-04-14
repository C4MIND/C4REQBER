/**
 * Export utilities for Canvas
 * PNG, PDF, JSON, SVG exports
 */

export interface ExportOptions {
  format: 'png' | 'svg' | 'pdf' | 'json';
  filename?: string;
  scale?: number;
  quality?: number;
}

export const exportCanvas = async (
  svgElement: SVGSVGElement,
  options: ExportOptions
): Promise<void> => {
  const { format, filename = 'turbo-cdi-export' } = options;
  
  switch (format) {
    case 'svg':
      await exportSVG(svgElement, filename);
      break;
    case 'png':
      await exportPNG(svgElement, filename, options.scale || 2);
      break;
    case 'pdf':
      await exportPDF(svgElement, filename);
      break;
    case 'json':
      await exportJSON(svgElement, filename);
      break;
  }
};

const exportSVG = async (svg: SVGSVGElement, filename: string): Promise<void> => {
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(svg);
  const blob = new Blob([svgString], { type: 'image/svg+xml' });
  downloadBlob(blob, `${filename}.svg`);
};

const exportPNG = async (
  svg: SVGSVGElement,
  filename: string,
  scale: number
): Promise<void> => {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d')!;
  
  const svgData = new XMLSerializer().serializeToString(svg);
  const svgSize = svg.getBoundingClientRect();
  
  canvas.width = svgSize.width * scale;
  canvas.height = svgSize.height * scale;
  
  const img = new Image();
  const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(svgBlob);
  
  await new Promise<void>((resolve) => {
    img.onload = () => {
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      resolve();
    };
    img.src = url;
  });
  
  canvas.toBlob((blob) => {
    if (blob) downloadBlob(blob, `${filename}.png`);
  }, 'image/png');
};

const exportPDF = async (svg: SVGSVGElement, filename: string): Promise<void> => {
  // Simple PDF export using jsPDF (would need to add dependency)
  // For now, convert to PNG and let user print to PDF
  await exportPNG(svg, filename, 2);
  console.log('PDF export: converted to high-res PNG. Use browser print to PDF.');
};

const exportJSON = async (svg: SVGSVGElement, filename: string): Promise<void> => {
  // Extract data attributes from SVG
  const data: Record<string, any> = {
    version: '6.0.0',
    timestamp: new Date().toISOString(),
    viewBox: svg.viewBox.baseVal,
    elements: [],
  };
  
  svg.querySelectorAll('[data-node-id]').forEach((el) => {
    data.elements.push({
      id: el.getAttribute('data-node-id'),
      type: el.getAttribute('data-type'),
      c4State: el.getAttribute('data-c4-state'),
      transform: el.getAttribute('transform'),
    });
  });
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  downloadBlob(blob, `${filename}.json`);
};

const downloadBlob = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

// Batch export for multiple simulations
export const exportSimulationReport = async (
  simulationResults: any[],
  filename: string = 'turbo-cdi-report'
): Promise<void> => {
  const report = {
    generatedAt: new Date().toISOString(),
    version: '6.0.0',
    simulations: simulationResults,
    summary: {
      total: simulationResults.length,
      avgConfidence: simulationResults.reduce((a, r) => a + (r.confidence || 0), 0) / simulationResults.length,
      patterns: [...new Set(simulationResults.map(r => r.patternId))],
    },
  };
  
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  downloadBlob(blob, `${filename}.json`);
};

export default exportCanvas;
