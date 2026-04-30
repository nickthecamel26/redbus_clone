import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Calendar, MapPin } from 'lucide-react'

function Home() {
  const navigate = useNavigate()
  const [searchData, setSearchData] = useState({
    source: '',
    destination: '',
    date: ''
  })

  const handleSearch = (e) => {
    e.preventDefault()
    const params = new URLSearchParams(searchData)
    navigate(`/search?${params.toString()}`)
  }

  return (
    <div className="min-h-[calc(100vh-200px)] bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-4xl">
        <h1 className="text-3xl font-bold text-gray-800 mb-2 text-center">
          Book Bus Tickets
        </h1>
        <p className="text-gray-600 text-center mb-8">
          Find the best bus deals for your journey
        </p>
        
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="From"
                value={searchData.source}
                onChange={(e) => setSearchData({...searchData, source: e.target.value})}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                required
              />
            </div>
            
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="To"
                value={searchData.destination}
                onChange={(e) => setSearchData({...searchData, destination: e.target.value})}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                required
              />
            </div>
            
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="date"
                value={searchData.date}
                onChange={(e) => setSearchData({...searchData, date: e.target.value})}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                required
              />
            </div>
          </div>
          
          <button
            type="submit"
            className="w-full md:w-auto md:px-12 py-3 bg-primary hover:bg-primary-dark text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 mx-auto"
          >
            <Search size={20} />
            Search Buses
          </button>
        </form>
      </div>
    </div>
  )
}

export default Home
