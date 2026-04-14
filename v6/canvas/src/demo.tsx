import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { C4VisualMap } from './components/C4VisualMap'
import type { C4State } from './types'

const App: React.FC = () => {
  const [selectedState, setSelectedState] = useState<string>('111')

  const handleStateSelect = (state: C4State) => {
    setSelectedState(state.code)
    console.log('Selected C4 state:', state)
  }

  return (
    <div style={{
      background: '#0f0f1a',
      minHeight: '100vh',
      padding: '20px',
      color: '#ffffff',
      fontFamily: 'monospace'
    }}>
      <header style={{ marginBottom: '20px' }}>
        <h1 style={{ 
          color: '#4ECDC4', 
          margin: 0,
          fontSize: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span>◈</span>
          TURBO-CDI v6.0 Canvas
        </h1>
        <p style={{ color: '#6c757d', margin: '5px 0 0 0' }}>
          C4 Cognitive Geometry Visual Map
        </p>
      </header>

      <main>
        <C4VisualMap
          width={1000}
          height={700}
          selectedState={selectedState}
          onStateSelect={handleStateSelect}
          showTransitions={true}
        />
      </main>

      <footer style={{ 
        marginTop: '20px', 
        padding: '15px',
        background: '#1a1a2e',
        borderRadius: '5px',
        fontSize: '12px',
        color: '#6c757d'
      }}>
        <div style={{ marginBottom: '10px', color: '#4ECDC4', fontWeight: 'bold' }}>
          NAVIGATION
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          <div>
            <strong style={{ color: '#ffffff' }}>Dimensions:</strong>
            <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
              <li>Time: Past → Present → Future</li>
              <li>Scale: Concrete → Abstract → Meta</li>
              <li>Agency: Self → Other → System</li>
            </ul>
          </div>
          <div>
            <strong style={{ color: '#ffffff' }}>Controls:</strong>
            <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
              <li>Click state to select</li>
              <li>Drag to pan</li>
              <li>Scroll to zoom</li>
              <li>Hover for details</li>
            </ul>
          </div>
          <div>
            <strong style={{ color: '#ffffff' }}>27 States:</strong>
            <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
              <li>Each state = unique cognitive perspective</li>
              <li>Transitions = creative transformations</li>
              <li>Selected: {selectedState}</li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Mount the app
const rootElement = document.getElementById('root')
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(<App />)
}

export default App
