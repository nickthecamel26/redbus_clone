'use client';

import { Suspense, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import axios from 'axios';
import { ArrowUpDown } from 'lucide-react';
import LocationAutocomplete from '@/components/LocationAutocomplete';
import TripCard from '@/components/trips/TripCard';
import { tripApi, TripSearchRequest } from '@/lib/api-client';

function SearchPageInner() {
  const router = useRouter();
  const urlParams = useSearchParams();

  // Hydrate form fields from URL on mount and on every URL change.
  // The home page navigates here with ?from=&to=&date= so users never type twice.
  const urlFrom = urlParams.get('from') ?? '';
  const urlTo = urlParams.get('to') ?? '';
  const urlDate = urlParams.get('date') ?? '';

  const [source, setSource] = useState(urlFrom);
  const [destination, setDestination] = useState(urlTo);
  const [travelDate, setTravelDate] = useState(urlDate);

  // Render-time sync for the date input. (LocationAutocomplete handles its own
  // sync via the `initialValue` prop.) Tracks the previous URL date so back/
  // forward navigation rehydrates the date field without a useEffect.
  const [lastUrlDate, setLastUrlDate] = useState(urlDate);
  if (urlDate !== lastUrlDate) {
    setLastUrlDate(urlDate);
    setTravelDate(urlDate);
  }

  // The search query is driven entirely by URL params. If all three are present,
  // the trips fetch fires automatically on mount — no extra click required.
  const searchParams = useMemo<TripSearchRequest | null>(() => {
    const from = urlParams.get('from');
    const to = urlParams.get('to');
    const date = urlParams.get('date');
    if (!from || !to || !date) return null;
    return { source: from, destination: to, travel_date: date };
  }, [urlParams]);

  const {
    data: trips = [],
    error,
    isLoading,
  } = useQuery({
    queryKey: ['trips', searchParams],
    queryFn: () => (searchParams ? tripApi.search(searchParams) : Promise.resolve([])),
    enabled: !!searchParams,
    retry: (failureCount, err) => {
      if (axios.isAxiosError(err) && err.response?.status === 429) {
        toast.error('Too many search attempts. Please try again in a minute.');
        return false;
      }
      return failureCount < 2;
    },
  });

  const handleSearch = () => {
    if (!source || !destination || !travelDate) {
      toast.error('Please fill in all search fields');
      return;
    }
    if (source.trim().toLowerCase() === destination.trim().toLowerCase()) {
      toast.error('Source and destination must be different');
      return;
    }

    // Update the URL without a full page reload. The useEffect + useMemo above
    // re-hydrate state and the query auto-refetches with the new params.
    const next = new URLSearchParams({ from: source, to: destination, date: travelDate });
    router.push(`/search?${next.toString()}`, { scroll: false });
  };

  const handleSwap = () => {
    setSource(destination);
    setDestination(source);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            Search Bus Tickets
          </h1>
          
          <div className="flex flex-col md:flex-row md:items-stretch border border-gray-200 rounded-lg divide-y md:divide-y-0 md:divide-x relative">
            <LocationAutocomplete
              id="results-from"
              label="From"
              value={source}
              onChange={setSource}
              initialValue={urlFrom}
              excludeValue={destination}
            />

            <div className="flex items-center justify-center px-2 bg-white">
              <button
                type="button"
                onClick={handleSwap}
                className="p-2 rounded-full bg-red-500 text-white hover:bg-red-600 transition-colors"
                title="Swap source and destination"
              >
                <ArrowUpDown className="h-4 w-4" />
              </button>
            </div>

            <LocationAutocomplete
              id="results-to"
              label="To"
              value={destination}
              onChange={setDestination}
              initialValue={urlTo}
              excludeValue={source}
            />

            <div className="flex-1 flex items-center p-5 group hover:bg-gray-50 transition">
              <div className="flex-1">
                <label htmlFor="results-date" className="block text-[10px] uppercase font-bold text-gray-500 tracking-wider">
                  Date
                </label>
                <input
                  id="results-date"
                  type="date"
                  value={travelDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setTravelDate(e.target.value)}
                  className="w-full text-lg font-semibold outline-none bg-transparent text-gray-700"
                />
              </div>
            </div>
          </div>

          <button
            onClick={handleSearch}
            disabled={isLoading}
            className="w-full mt-6 bg-red-500 text-white py-3 px-4 rounded-md hover:bg-red-600 disabled:bg-gray-400 transition-colors duration-200 font-medium"
          >
            {isLoading ? 'Searching...' : 'Search Buses'}
          </button>
        </div>

        {/* Search Results */}
        {trips.length > 0 && (
          <div className="mt-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">
              Available Trips ({trips.length})
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {trips.map((trip) => (
                <TripCard
                  key={trip.id}
                  trip={trip}
                  onSelectTrip={(tripId) => console.log('Selected trip:', tripId)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Error Handling */}
        {error && !isLoading && (
          <div className="mt-8 bg-red-50 border border-red-200 rounded-md p-4">
            <h3 className="text-lg font-medium text-red-800">Search Error</h3>
            <p className="mt-2 text-red-600">
              {axios.isAxiosError(error) && error.response?.status === 429 
                ? 'Too many search attempts. Please try again in a minute.'
                : 'Failed to search for trips. Please try again.'}
            </p>
          </div>
        )}

        {/* No Results */}
        {!isLoading && !error && trips.length === 0 && searchParams && (
          <div className="mt-8 text-center">
            <h3 className="text-lg font-medium text-gray-900">No trips found</h3>
            <p className="mt-2 text-gray-600">
              Try adjusting your search criteria or travel dates.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  // useSearchParams() needs a Suspense boundary in the App Router.
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-500">Loading search…</div>}>
      <SearchPageInner />
    </Suspense>
  );
}
