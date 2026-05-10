'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Calendar, Search } from 'lucide-react';
import LocationAutocomplete from '@/components/LocationAutocomplete';
import { locationApi } from '@/lib/api-client';

export default function Home() {
  const router = useRouter();
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [date, setDate] = useState('');

  // Same queryKey as <LocationAutocomplete> — TanStack Query dedupes the request.
  const { data: cities = [] } = useQuery({
    queryKey: ['locations'],
    queryFn: () => locationApi.getAll(),
    staleTime: 5 * 60 * 1000,
  });

  // Build a case-insensitive lookup so validation matches what the dropdown shows.
  const cityLookup = useMemo(
    () => new Set(cities.map((c) => c.toLowerCase())),
    [cities]
  );

  const isValidFrom = cityLookup.has(from.trim().toLowerCase());
  const isValidTo = cityLookup.has(to.trim().toLowerCase());
  const canSearch = isValidFrom && isValidTo && Boolean(date) && from.trim().toLowerCase() !== to.trim().toLowerCase();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSearch) return;
    const params = new URLSearchParams({ from, to, date });
    router.push(`/search?${params.toString()}`);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      {/* 1. Navigation Header */}
      <nav className="bg-[#D84E55] p-4 text-white shadow-lg">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => router.push('/')}>
            <div className="bg-white text-[#D84E55] px-2 py-1 rounded-md font-black text-xl italic">
              rb
            </div>
            <h1 className="text-2xl font-bold tracking-tight">redBus</h1>
          </div>
          <div className="flex items-center space-x-6 text-sm font-semibold">
            <span className="hover:underline cursor-pointer">Help</span>
            <span className="hover:underline cursor-pointer">Manage Booking</span>
            <button className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition">
              Login / Signup
            </button>
          </div>
        </div>
      </nav>

      {/* 2. Hero & Search Section */}
      <div className="relative h-[450px] bg-gradient-to-r from-[#D84E55] to-[#A32A31] flex flex-col items-center justify-center px-4">
        <h2 className="text-4xl font-extrabold text-white mb-10 text-center drop-shadow-md">
          {"India's No. 1 Online Bus Ticket Booking Site"}
        </h2>

        {/* 3. Search Bar Form */}
        <form 
          onSubmit={handleSearch}
          className="bg-white w-full max-w-5xl rounded-2xl shadow-2xl flex flex-col md:flex-row items-stretch divide-y md:divide-y-0 md:divide-x border border-gray-200 relative"
        >
          <LocationAutocomplete
            id="search-from"
            label="From"
            value={from}
            onChange={setFrom}
            excludeValue={to}
          />

          <LocationAutocomplete
            id="search-to"
            label="To"
            value={to}
            onChange={setTo}
            excludeValue={from}
          />

          <div className="flex-1 flex items-center p-5 group hover:bg-gray-50 transition">
            <Calendar className="text-gray-400 mr-3 group-hover:text-[#D84E55]" size={24} />
            <div className="flex-1">
              <label className="block text-[10px] uppercase font-bold text-gray-500 tracking-wider">Date</label>
              <input 
                type="date" 
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full text-lg font-semibold outline-none bg-transparent text-gray-700"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={!canSearch}
            aria-disabled={!canSearch}
            title={canSearch ? 'Search buses' : 'Pick a valid From, To, and Date to continue'}
            className="bg-[#D84E55] hover:bg-[#C13D44] disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-10 py-6 md:py-0 font-black text-xl transition-all flex items-center justify-center gap-2"
          >
            <Search size={24} strokeWidth={3} />
            SEARCH
          </button>
        </form>
      </div>

      {/* 4. Footnote Section */}
      <div className="max-w-6xl mx-auto py-16 px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center text-gray-400">
           <p>2000+ Bus Operators</p>
           <p>Easy Booking</p>
           <p>Secure Payments</p>
        </div>
      </div>
    </main>
  );
}