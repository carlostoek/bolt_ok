/**
 * Main App Component
 */

import Header from './components/Header';
import NarrativeCanvas from './components/NarrativeCanvas';
import PropertiesPanel from './components/PropertiesPanel';

function App() {
  return (
    <div className="h-screen w-screen flex flex-col">
      <Header />
      <main className="flex-1 overflow-hidden flex">
        <div className="flex-1">
          <NarrativeCanvas />
        </div>
        <PropertiesPanel />
      </main>
    </div>
  );
}

export default App;
