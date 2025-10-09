/**
 * Main App Component
 */

import Header from './components/Header';
import NarrativeCanvas from './components/NarrativeCanvas';

function App() {
  return (
    <div className="h-screen w-screen flex flex-col">
      <Header />
      <main className="flex-1 overflow-hidden">
        <NarrativeCanvas />
      </main>
    </div>
  );
}

export default App;
