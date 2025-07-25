import React, { useEffect, useRef, useState } from 'react';
import type { NetworkVisualizationProps } from '../../lib/types';

// Note: These will be available after npm install
// import cytoscape from 'cytoscape';
// import cose from 'cytoscape-cose';

export const NetworkVisualization: React.FC<NetworkVisualizationProps> = ({
  data,
  onNodeSelect,
  onEdgeSelect,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeCytoscape = async () => {
      if (!containerRef.current) return;

      try {
        // Dynamic import to handle missing dependencies
        const cytoscape = await import('cytoscape').catch(() => null);
        const coseBilkent = await import('cytoscape-cose-bilkent' as any).catch(() => null);

        if (!cytoscape) {
          setError('Cytoscape.js is not installed. Please run: npm install');
          setIsLoading(false);
          return;
        }

        // Register extensions
        if (coseBilkent) {
          cytoscape.default.use(coseBilkent.default);
        }

        // Initialize Cytoscape
        cyRef.current = cytoscape.default({
          container: containerRef.current,
          elements: data?.elements || [],
          style: [
            {
              selector: 'node',
              style: {
                'background-color': '#666',
                'label': 'data(label)',
                'text-valign': 'center',
                'text-halign': 'center',
                'color': '#fff',
                'text-outline-width': 2,
                'text-outline-color': '#666',
                'font-size': '12px',
                'width': '30px',
                'height': '30px',
              },
            },
            {
              selector: 'node:selected',
              style: {
                'background-color': '#61bffc',
                'border-width': 3,
                'border-color': '#61bffc',
              },
            },
            {
              selector: 'edge',
              style: {
                'width': 2,
                'line-color': '#ccc',
                'target-arrow-color': '#ccc',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
              },
            },
            {
              selector: 'edge:selected',
              style: {
                'line-color': '#61bffc',
                'target-arrow-color': '#61bffc',
                'width': 3,
              },
            },
          ],
          layout: {
            name: coseBilkent ? 'cose-bilkent' : 'grid',
            animate: true,
            animationDuration: 500,
          },
          wheelSensitivity: 0.1,
          minZoom: 0.1,
          maxZoom: 3,
        });

        // Add event listeners
        cyRef.current.on('tap', 'node', (evt: any) => {
          const node = evt.target;
          const nodeId = node.id();
          onNodeSelect?.(nodeId);
        });

        cyRef.current.on('tap', 'edge', (evt: any) => {
          const edge = evt.target;
          const edgeId = edge.id();
          onEdgeSelect?.(edgeId);
        });

        setIsLoading(false);
      } catch (err) {
        console.error('Failed to initialize Cytoscape:', err);
        setError('Failed to initialize network visualization');
        setIsLoading(false);
      }
    };

    initializeCytoscape();

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (cyRef.current && data) {
      try {
        // Update elements
        cyRef.current.elements().remove();
        cyRef.current.add(data.elements);
        
        // Run layout
        cyRef.current.layout({
          name: 'cose-bilkent',
          animate: true,
          animationDuration: 500,
        }).run();
      } catch (err) {
        console.error('Failed to update network data:', err);
      }
    }
  }, [data]);

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 ${className}`}>
        <div className="text-center">
          <div className="text-red-600 mb-2">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.732 15.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">ネットワークを読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <div ref={containerRef} className="w-full h-full" />
      {!data?.elements?.length && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="text-gray-400 mb-2">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <p className="text-gray-600">表示するネットワークデータがありません</p>
          </div>
        </div>
      )}
    </div>
  );
};