'use client';

import { useState, useMemo } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { toast } from 'react-hot-toast';
import SeatGrid from './SeatGrid';
import { type Trip, bookingApi, tripApi } from '@/lib/api-client';

type SeatState = 'available' | 'booked' | 'selected';

interface SeatSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  trip: Trip;
}

export default function SeatSelectionModal({ 
  isOpen, 
  onClose, 
  trip 
}: SeatSelectionModalProps) {
  const [selectedSeats, setSelectedSeats] = useState<string[]>([]);
  const queryClient = useQueryClient();

  const { data: backendSeats = [], isLoading: seatsLoading } = useQuery({
    queryKey: ['trip-seats', trip.id],
    queryFn: () => tripApi.getTripSeats(trip.id),
    enabled: isOpen,
  });

  const seatsWithSelection = useMemo(() => {
    const transformed = backendSeats.map((seat: { seat_number: string; is_available: boolean }) => ({
      id: seat.seat_number,
      state: seat.is_available ? 'available' : 'booked'
    }));

    return transformed.map((seat: { id: string; state: SeatState }) => ({
      ...seat,
      state: selectedSeats.includes(seat.id) ? 'selected' : seat.state
    }));
  }, [backendSeats, selectedSeats]);

  const bookingMutation = useMutation({
    mutationFn: async ({ tripId, seatNumbers, totalAmount }: { tripId: number; seatNumbers: string[]; totalAmount: number }) => {
      return await bookingApi.createBooking(tripId, seatNumbers, totalAmount);
    },
    onSuccess: () => {
      toast.success('Booking successful! 🎉');
      // Force refresh of seat grid for this trip so newly-booked seats appear as "Booked"
      queryClient.invalidateQueries({ queryKey: ['trip-seats', trip.id] });
      queryClient.invalidateQueries({ queryKey: ['trip', trip.id] });
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
      queryClient.invalidateQueries({ queryKey: ['my-bookings'] });
      setSelectedSeats([]);
      onClose();
    },
    onError: (error: unknown) => {
      let errorMessage = 'Booking failed.';
      
      if (error && typeof error === 'object') {
        const errorObj = error as { response?: { data?: { detail?: string } }; message?: string };
        errorMessage = errorObj.response?.data?.detail || errorObj.message || errorMessage;
      } else if (error && typeof error === 'string') {
        errorMessage = error;
      }
      
      toast.error(errorMessage, { duration: 5000 });
    },
  });

  const handleSeatClick = (seatId: string) => {
    setSelectedSeats(prev => 
      prev.includes(seatId) ? prev.filter(id => id !== seatId) : [...prev, seatId]
    );
  };

  const totalAmount = selectedSeats.length * trip.price;

  const handleConfirmSelection = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    
    if (!token) {
      toast.error('Please login to continue');
      window.location.href = '/login';
      return;
    }

    if (selectedSeats.length === 0) {
      toast.error('Please select at least one seat');
      return;
    }
    
    bookingMutation.mutate({
      tripId: trip.id,
      seatNumbers: selectedSeats,
      totalAmount: totalAmount
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="bg-red-500 text-white p-4 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold">Select Seats</h2>
            <p className="text-sm opacity-90">
              {trip.bus_name} • {trip.available_seats} seats available
            </p>
          </div>
          <button onClick={onClose} className="hover:bg-red-600 p-2 rounded-lg transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex flex-col lg:flex-row">
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Choose Your Seats</h3>
              <p className="text-sm text-gray-600">Click on available seats to select them</p>
            </div>
            
            {seatsLoading ? (
              <div className="flex justify-center p-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-500"></div>
              </div>
            ) : (
              <SeatGrid
                seats={seatsWithSelection}
                onSeatClick={handleSeatClick}
                tripPrice={trip.price}
              />
            )}
          </div>

          <div className="lg:w-80 bg-gray-50 p-6 border-t lg:border-t-0 lg:border-l border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Booking Summary</h3>
            <div className="flex justify-between text-lg font-bold text-gray-900 mb-6">
              <span>Total:</span>
              <span className="text-red-600">₹{totalAmount.toLocaleString('en-IN')}</span>
            </div>
            <button
              onClick={handleConfirmSelection}
              disabled={bookingMutation.isPending || selectedSeats.length === 0}
              className="w-full bg-red-500 text-white py-3 rounded-md font-bold hover:bg-red-600 disabled:bg-gray-300 transition-all"
            >
              {bookingMutation.isPending ? 'Processing...' : 'Proceed with Booking'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
