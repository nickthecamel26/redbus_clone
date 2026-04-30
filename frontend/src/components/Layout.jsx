import { Link } from 'react-router-dom'
import { Bus } from 'lucide-react'

function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-primary text-white shadow-lg">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-2xl font-bold">
            <Bus size={32} />
            RedBus Clone
          </Link>
          <div className="flex gap-6">
            <Link to="/" className="hover:text-primary-light transition-colors">
              Home
            </Link>
            <Link to="/search" className="hover:text-primary-light transition-colors">
              Search
            </Link>
          </div>
        </div>
      </nav>
      
      <main className="flex-1">
        {children}
      </main>
      
      <footer className="bg-gray-800 text-white py-6">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; 2024 RedBus Clone. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

export default Layout
