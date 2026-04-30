import { useSearchParams } from 'react-router-dom'
import { Bus, Clock, Star } from 'lucide-react'

function Search() {
  const [searchParams] = useSearchParams()
  const source = searchParams.get('source')
  const destination = searchParams.get('destination')
  const date = searchParams.get('date')

  // Placeholder bus data
  const buses = [
    {
      id: 1,
      operator: 'Royal Travels',
      type: 'AC Sleeper',
      departure: '21:00',
      arrival: '06:00',
      duration: '9h 00m',
      rating: 4.5,
      price: 899,
      seats: 12
    },
    {
      id: 2,
      operator: 'National Express',
      type: 'Non-AC Seater',
      departure: '22:30',
      arrival: '07:30',
      duration: '9h 00m',
      rating: 4.2,
      price: 599,
      seats: 8
    },
    {
      id: 3,
      operator: 'Green Line',
      type: 'AC Seater',
      departure: '20:00',
      arrival: '05:00',
      duration: '9h 00m',
      rating: 4.7,
      price: 749,
      seats: 15
    }
  ]

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {source || 'Source'} <span className="text-primary">→</span> {destination || 'Destination'}
            </h1>
            <p className="text-gray-600">{date || 'Today'}</p>
          </div>
          <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            Modify
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {buses.map((bus) => (
          <div key={bus.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-bold text-lg">{bus.operator}</h3>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-sm rounded-full flex items-center gap-1">
                    <Star size={14} fill="currentColor" />
                    {bus.rating}
                  </span>
                </div>
                <p className="text-gray-600 text-sm">{bus.type}</p>
              </div>

              <div className="flex items-center gap-8 text-center">
                <div>
                  <p className="text-xl font-bold">{bus.departure}</p>
                  <p className="text-sm text-gray-600">{source || 'Source'}</p>
                </div>
                <div className="text-gray-400">
                  <Clock size={16} className="mx-auto mb-1" />
                  <p className="text-sm">{bus.duration}</p>
                </div>
                <div>
                  <p className="text-xl font-bold">{bus.arrival}</p>
                  <p className="text-sm text-gray-600">{destination || 'Dest'}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-800">₹{bus.price}</p>
                  <p className="text-sm text-gray-500">{bus.seats} seats left</p>
                </div>
                <button className="px-6 py-3 bg-primary hover:bg-primary-dark text-white font-semibold rounded-lg transition-colors">
                  Book
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Search
