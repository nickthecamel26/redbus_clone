'use client';

import { ArrowUpDownIcon } from 'lucide-react';

interface SearchBarProps {
  source: string;
  destination: string;
  travelDate: string;
  onSourceChange: (source: string) => void;
  onDestinationChange: (destination: string) => void;
  onTravelDateChange: (date: string) => void;
  onSwap: () => void;
}

export default function SearchBar({
  source,
  destination,
  travelDate,
  onSourceChange,
  onDestinationChange,
  onTravelDateChange,
  onSwap,
}: SearchBarProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Source City */}
        <div>
          <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-2">
            From
          </label>
          <div className="relative">
            <input
              type="text"
              id="source"
              value={source}
              onChange={(e) => onSourceChange(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent text-slate-900 placeholder:text-slate-400"
              placeholder="Enter source city"
            />
            </div>
        </div>

        {/* Swap Button */}
        <div className="flex items-center justify-center">
          <button
            type="button"
            onClick={onSwap}
            className="p-2 rounded-full bg-red-500 text-white hover:bg-red-600 transition-colors duration-200"
            title="Swap source and destination"
          >
            <ArrowUpDownIcon className="h-4 w-4" />
          </button>
        </div>

        {/* Destination City */}
        <div>
          <label htmlFor="destination" className="block text-sm font-medium text-gray-700 mb-2">
            To
          </label>
          <div className="relative">
            <input
              type="text"
              id="destination"
              value={destination}
              onChange={(e) => onDestinationChange(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent text-slate-900 placeholder:text-slate-400"
              placeholder="Enter destination city"
            />
          </div>
        </div>

        {/* Travel Date */}
        <div>
          <label htmlFor="travelDate" className="block text-sm font-medium text-gray-700 mb-2">
            Travel Date
          </label>
          <input
            type="date"
            id="travelDate"
            value={travelDate}
            onChange={(e) => onTravelDateChange(e.target.value)}
            min={new Date().toISOString().split('T')[0]}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent text-slate-900 placeholder:text-slate-400"
          />
        </div>
      </div>
    </div>
  );
}
