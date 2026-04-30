import { useState } from 'react'
import { SeatRow } from '../components/SeatRow'
import { ArrowLeft, Shield } from 'lucide-react'
import { Link } from 'react-router-dom'

function Booking() {
  const [selectedSeats, setSelectedSeats] = useState([])
  const seatPrice = 899

  const toggleSeat = (seat) => {
    if (selectedSeats.includes(seat)) {
      setSelectedSeats(selectedSeats.filter(s => s !== seat))
    } else {
      setSelectedSeats([...selectedSeats, seat])
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/search" className="flex items-center gap-2 text-gray-600 hover:text-primary mb-6">
        <ArrowLeft size={20} />
        Back to Search
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold mb-4">Select Seats</h2>
            
            <div className="flex items-center gap-6 mb-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 border-2 border-gray-300 rounded"></div>
                <span>Available</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-primary rounded"></div>
                <span>Selected</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-gray-300 rounded"></div>
                <span>Booked</span>
              </div>
            </div>

            <div className="space-y-2">
              {['A', 'B', 'C', 'D', 'E', 'F'].map((row) => (
                <SeatRow
                  key={row}
                  row={row}
                  selectedSeats={selectedSeats}
                  onToggle={toggleSeat}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
            <h2 className="text-xl font-bold mb-4">Booking Summary</h2>
            
            <div className="space-y-3 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Royal Travels</span>
                <span className="font-medium">AC Sleeper</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Seats</span>
                <span className="font-medium">{selectedSeats.join(', ') || '-'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Base Fare</span>
                <span className="font-medium">₹{selectedSeats.length * seatPrice}</span>
              </div>
            </div>

            <div className="border-t pt-4 mb-6">
              <div className="flex items-center gap-2 text-sm text-green-700 mb-4">
                <Shield size={16} />
                <span>Safe and secure booking</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-lg font-bold">Total</span>
                <span className="text-2xl font-bold text-primary">
                  ₹{selectedSeats.length * seatPrice}
                </span>
              </div>
            </div>

            <button
              disabled={selectedSeats.length === 0}
              className="w-full py-3 bg-primary hover:bg-primary-dark disabled:bg-gray-300 text-white font-semibold rounded-lg transition-colors"
            >
              Proceed to Pay
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Booking
