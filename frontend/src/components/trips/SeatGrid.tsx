'use client';

import { useMemo } from 'react';
import { User, X } from 'lucide-react';

type SeatState = 'available' | 'booked' | 'selected';

interface Seat {
  id: string;
  state: SeatState;
  isWindow?: boolean;
}

interface SeatGridProps {
  seats: Seat[];
  onSeatClick: (seatId: string) => void;
  tripPrice: number;
}

// Parse a seat_number into a sortable row + column key.
// Handles all backend formats: "1A", "A1", "L1", "U1", "S1", and pure-numeric.
// Returns rowKey (used to group rows) and colKey (used to sort within a row).
function parseSeatId(id: string): { rowKey: string; colKey: number } {
  // Format 1: digit-letter (e.g., "1A", "12C") — row = digits, col = letter ordinal
  const digitFirst = id.match(/^(\d+)([A-Za-z]+)$/);
  if (digitFirst) {
    return {
      rowKey: digitFirst[1].padStart(4, '0'),
      colKey: digitFirst[2].toUpperCase().charCodeAt(0),
    };
  }
  // Format 2: letter-digit (e.g., "A1", "L1", "U2") — row = letter, col = digits
  const letterFirst = id.match(/^([A-Za-z]+)(\d+)$/);
  if (letterFirst) {
    return {
      rowKey: letterFirst[1].toUpperCase(),
      colKey: parseInt(letterFirst[2], 10),
    };
  }
  // Format 3: pure numeric (e.g., "1", "42")
  if (/^\d+$/.test(id)) {
    return { rowKey: '0000', colKey: parseInt(id, 10) };
  }
  // Fallback: treat as single-row anything-goes
  return { rowKey: 'ZZZ', colKey: 0 };
}

export default function SeatGrid({ seats, onSeatClick }: SeatGridProps) {
  // Deduplicate the incoming seats array by id BEFORE any grouping.
  // Defends against backend duplicates or stale React Query merges that would
  // otherwise produce duplicate React keys and break click mapping.
  const uniqueSeats = useMemo(
    () => Array.from(new Map(seats.map((s) => [s.id, s])).values()),
    [seats]
  );

  // Group seats by row, derived from each seat's own ID. Format-agnostic.
  // Every seat is rendered from its own backend object — no index-based positioning.
  const seatRows = useMemo(() => {
    const groups = new Map<string, Seat[]>();
    for (const seat of uniqueSeats) {
      const { rowKey } = parseSeatId(seat.id);
      if (!groups.has(rowKey)) groups.set(rowKey, []);
      groups.get(rowKey)!.push(seat);
    }
    // Sort seats within each row by colKey
    for (const row of groups.values()) {
      row.sort((a, b) => parseSeatId(a.id).colKey - parseSeatId(b.id).colKey);
    }
    // Sort rows by rowKey
    return Array.from(groups.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([, rowSeats]) => rowSeats);
  }, [uniqueSeats]);

  const getSeatClasses = (state: SeatState) => {
    const base = 'w-10 h-10 border-2 rounded flex items-center justify-center transition-colors select-none';
    switch (state) {
      case 'available':
        return `${base} border-gray-300 bg-gray-100 hover:border-red-500 hover:bg-red-50 cursor-pointer`;
      case 'booked':
        return `${base} border-gray-300 bg-gray-200 opacity-60 cursor-not-allowed`;
      case 'selected':
        return `${base} border-red-500 bg-red-500 text-white cursor-pointer`;
      default:
        return base;
    }
  };

  const handleClick = (seat: Seat) => {
    // Strict guard: only 'available' or 'selected' (already picked by this user) are clickable.
    // 'booked' seats are strictly ignored.
    if (seat.state === 'booked') return;
    // Diagnostic: log the EXACT seat ID the user clicked, sourced from the seat object.
    console.log('User clicking seat:', seat.id);
    onSeatClick(seat.id);
  };

  return (
    <div className="bg-white rounded-lg p-6 shadow-md">
      {/* Bus Header with Driver Icon */}
      <div className="flex justify-end mb-4">
        <div className="flex items-center space-x-2 text-gray-600">
          <User className="w-5 h-5" />
          <span className="text-sm font-medium">Driver</span>
        </div>
      </div>

      {/* Seat Layout — data-driven from API response */}
      <div className="space-y-3">
        {seatRows.length === 0 ? (
          <div className="text-center text-gray-500 py-8">No seats available</div>
        ) : (
          seatRows.map((row, rowIndex) => {
            // Split row at midpoint for aisle rendering. Format-agnostic —
            // works regardless of seat_number style. The aisle is purely visual
            // and is NOT a clickable element — it cannot interfere with seat data.
            const mid = Math.ceil(row.length / 2);
            const leftSeats = row.slice(0, mid);
            const rightSeats = row.slice(mid);

            return (
              <div key={`row-${rowIndex}`} className="flex items-center justify-center gap-6">
                {/* Left side seats */}
                <div className="flex items-center gap-2">
                  {leftSeats.map((seat, index) => (
                    <button
                      key={`${seat.id}-L-${rowIndex}-${index}`}
                      type="button"
                      disabled={seat.state === 'booked'}
                      onClick={() => handleClick(seat)}
                      aria-label={`Seat ${seat.id} — ${seat.state}`}
                      className={getSeatClasses(seat.state)}
                    >
                      {seat.state === 'booked' ? (
                        <X className="w-4 h-4 text-red-500" />
                      ) : (
                        <span className="text-[10px] font-semibold">{seat.id}</span>
                      )}
                    </button>
                  ))}
                </div>

                {/* Aisle */}
                <div className="w-8 h-10 border-l-2 border-r-2 border-dashed border-gray-300 flex items-center justify-center">
                  <span className="text-[9px] text-gray-400 font-medium rotate-90">AISLE</span>
                </div>

                {/* Right side seats */}
                <div className="flex items-center gap-2">
                  {rightSeats.map((seat, index) => (
                    <button
                      key={`${seat.id}-R-${rowIndex}-${index}`}
                      type="button"
                      disabled={seat.state === 'booked'}
                      onClick={() => handleClick(seat)}
                      aria-label={`Seat ${seat.id} — ${seat.state}`}
                      className={getSeatClasses(seat.state)}
                    >
                      {seat.state === 'booked' ? (
                        <X className="w-4 h-4 text-red-500" />
                      ) : (
                        <span className="text-[10px] font-semibold">{seat.id}</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Legend */}
      <div className="mt-8 pt-4 border-t border-gray-200">
        <div className="flex justify-center space-x-6 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 border-2 border-gray-300 rounded flex items-center justify-center">
              <div className="w-4 h-4 bg-gray-200 rounded"></div>
            </div>
            <span className="text-gray-600">Available</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 border-2 border-red-500 rounded flex items-center justify-center bg-red-50">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
            </div>
            <span className="text-gray-600">Selected</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 border-2 border-gray-300 rounded flex items-center justify-center opacity-50">
              <X className="w-3 h-3 text-red-500" />
            </div>
            <span className="text-gray-600">Booked</span>
          </div>
        </div>
      </div>
    </div>
  );
}
