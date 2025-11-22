import { NarrativeEditor } from "./components/NarrativeEditor";
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <div className="container mx-auto p-4 md:p-8">
      <main>
        <NarrativeEditor />
      </main>
      <Toaster />
    </div>
  );
}

export default App;
