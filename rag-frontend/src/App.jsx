import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { ChatInterface } from './components/ChatInterface';

function App() {
  	const [sidebarOpen, setSidebarOpen] = useState(false);
  	const toggleSidebar = () => setSidebarOpen(prev=>!prev);

  	return (
		<div className='app-container'>
			<DocumentsSidebar/>
			<ChatInterface/>
		</div> 
	)
}

export default App
