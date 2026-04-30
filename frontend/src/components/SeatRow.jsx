export function SeatRow({ row, selectedSeats, onToggle }) {
  const seats = ['1', '2', '3', '4']
  
  return (
    <div className="flex items-center justify-center gap-4">
      <div className="flex gap-2">
        {seats.slice(0, 2).map((num) => {
          const seatId = `${row}${num}`
          const isSelected = selectedSeats.includes(seatId)
          
          return (
            <button
              key={seatId}
              onClick={() => onToggle(seatId)}
              className={`w-10 h-10 rounded border-2 font-medium text-sm transition-colors
                ${isSelected 
                  ? 'bg-primary border-primary text-white' 
                  : 'border-gray-300 hover:border-primary text-gray-700'
                }`}
            >
              {seatId}
            </button>
          )
        })}
      </div>
      
      <div className="w-8"></div>
      
      <div className="flex gap-2">
        {seats.slice(2).map((num) => {
          const seatId = `${row}${num}`
          const isSelected = selectedSeats.includes(seatId)
          
          return (
            <button
              key={seatId}
              onClick={() => onToggle(seatId)}
              className={`w-10 h-10 rounded border-2 font-medium text-sm transition-colors
                ${isSelected 
                  ? 'bg-primary border-primary text-white' 
                  : 'border-gray-300 hover:border-primary text-gray-700'
                }`}
            >
              {seatId}
            </button>
          )
        })}
      </div>
    </div>
  )
}
