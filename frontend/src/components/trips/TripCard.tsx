'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import SeatGrid from './SeatGrid';
import SeatSelectionModal from './SeatSelectionModal';
import { Trip, tripApi } from '@/lib/api-client';

interface TripCardProps {
  trip: Trip;
  onSelectTrip: (tripId: number) => void;
}

function TripCard({ trip, onSelectTrip }: TripCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const formatTime = (timeString: string) => {
    const date = new Date(timeString);
    return date.toLocaleTimeString('en-IN', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const formatDate = (timeString: string) => {
    const date = new Date(timeString);
    return date.toLocaleDateString('en-IN', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Fetch real seat data from backend
  const { data: availableSeats = [], isLoading: seatsLoading } = useQuery({
    queryKey: ['trip-seats', trip.id],
    queryFn: () => tripApi.getTripSeats(trip.id),
    enabled: isModalOpen,
  });

  return (
    <>
      <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-300 cursor-pointer border border-gray-200">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{trip.bus_name}</h3>
            <p className="text-sm text-gray-600">
              {trip.departure_time.split('T')[0]} → {trip.arrival_time.split('T')[0]}
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-red-600">
              ₹{trip.price.toLocaleString('en-IN')}
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-600">Departure</p>
            <p className="text-lg font-medium">{formatTime(trip.departure_time)}</p>
            <p className="text-sm text-gray-500">{formatDate(trip.departure_time)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Arrival</p>
            <p className="text-lg font-medium">{formatTime(trip.arrival_time)}</p>
            <p className="text-sm text-gray-500">{formatDate(trip.arrival_time)}</p>
          </div>
        </div>
        
        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
          <div>
            <p className="text-sm text-gray-600">Available Seats</p>
            <p className="text-xl font-bold text-green-600">{trip.available_seats}</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-6 py-3 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors duration-200 font-medium"
          >
            Select Seats
          </button>
        </div>
      </div>

      {/* Seat Selection Modal */}
      <SeatSelectionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        trip={trip}
      />
    </>
  );
}

export default TripCard;
