import { useState } from 'react';
import { ChatInterface, DocumentsSidebar } from './components';
import { Menu, X } from 'lucide-react'; // Assuming you have lucide-react installed

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-zinc-900 text-zinc-100">
      {/* Mobile Sidebar Toggle Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Container - Responsive logic included */}
      <div className={`
        fixed inset-y-0 left-0 z-30 w-80 transform transition-transform duration-300 ease-in-out bg-zinc-950 border-r border-white/10
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        md:relative md:translate-x-0
      `}>
        <DocumentsSidebar />
      </div>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative min-w-0">
        {/* Mobile Header / Toggle Button */}
        <div className="md:hidden h-14 flex items-center px-4 border-b border-white/10 bg-zinc-900">
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-white/5 rounded-md"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <span className="ml-3 font-semibold">AI Chat</span>
        </div>

        <ChatInterface />
      </main>
    </div>
  );
}

export default App;