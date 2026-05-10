'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, MapPin } from 'lucide-react';
import { locationApi } from '@/lib/api-client';

/**
 * Emergency fallback shown if the /trips/locations API call fails. Guarantees
 * the user can still pick a few popular cities even if the backend is down,
 * so the search form never looks broken.
 */
const FALLBACK_CITIES = [
  'Bangalore',
  'Chennai',
  'Coimbatore',
  'Hyderabad',
  'Madurai',
  'Mumbai',
  'Pune',
  'Trivandrum',
];

interface LocationAutocompleteProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  /** Cities to hide from the suggestion list (e.g. the "From" city when picking "To"). */
  excludeValue?: string;
  /** Stable id used for aria-controls / focus management. */
  id?: string;
  /**
   * Optional URL-driven seed. When this prop changes (e.g. the parent reads
   * a new value from useSearchParams() after a back/forward navigation), the
   * component pushes that value into the controlled `value` via `onChange`.
   * This keeps the input in sync with the URL without requiring useEffect.
   */
  initialValue?: string;
}

export default function LocationAutocomplete({
  label,
  value,
  onChange,
  placeholder = 'Enter City',
  excludeValue,
  id,
  initialValue,
}: LocationAutocompleteProps) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Render-time sync: when the parent's `initialValue` (typically derived from
  // a URL search param) changes, mirror it into the controlled value. Uses the
  // canonical "track previous prop" pattern so we don't need a useEffect that
  // would cause a cascading re-render.
  const [lastInitial, setLastInitial] = useState(initialValue);
  if (initialValue !== undefined && initialValue !== lastInitial) {
    setLastInitial(initialValue);
    if (initialValue !== value) {
      onChange(initialValue);
    }
  }

  // Fetch the master city list once and cache for the session.
  // Goes through the shared axios `api` instance (baseURL = http://localhost:8001/api/v1)
  // so we never hand-build URLs and inherit auth/rate-limit interceptors for free.
  const { data: apiCities, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['locations'],
    queryFn: () => locationApi.getAll(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // If the API call fails, fall back to the emergency hardcoded list so the
  // dropdown always has *something* to show. `usingFallback` drives a banner.
  const cities = useMemo(
    () => apiCities ?? (isError ? FALLBACK_CITIES : []),
    [apiCities, isError]
  );
  const usingFallback = isError && !apiCities;

  // Filter cities by user input. Substring match is case-insensitive.
  // When the input is empty, expose the first 5 as "Popular Cities".
  const query = value.trim().toLowerCase();
  const isFiltering = query.length > 0;

  const suggestions = useMemo(() => {
    const eligible = cities.filter((city) => city !== excludeValue);
    if (!isFiltering) return eligible.slice(0, 5); // Popular Cities
    return eligible
      .filter((city) => city.toLowerCase().includes(query))
      .slice(0, 8); // cap filtered dropdown size
  }, [cities, query, isFiltering, excludeValue]);

  // Close the dropdown when the user clicks outside the component.
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectCity = (city: string) => {
    onChange(city);
    setOpen(false);
    setActiveIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') setOpen(true);
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      if (activeIndex >= 0 && suggestions[activeIndex]) {
        e.preventDefault();
        selectCity(suggestions[activeIndex]);
      }
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div ref={wrapperRef} className="relative flex-1 flex items-center p-5 group hover:bg-gray-50 transition">
      <MapPin className="text-gray-400 mr-3 group-hover:text-[#D84E55]" size={24} />
      <div className="flex-1">
        <label htmlFor={id} className="block text-[10px] uppercase font-bold text-gray-500 tracking-wider">
          {label}
        </label>
        <input
          id={id}
          type="text"
          autoComplete="off"
          placeholder={placeholder}
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setOpen(true);
            // Reset highlight when the suggestion list shape changes.
            setActiveIndex(-1);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={id ? `${id}-listbox` : undefined}
          className="w-full text-lg font-semibold outline-none bg-transparent"
        />
      </div>

      {/* Force the dropdown open while the request is in flight or errored out
          so the user always sees feedback (spinner / fallback list / retry). */}
      {(open || isLoading || isError) && (
        <div
          id={id ? `${id}-listbox` : undefined}
          className="absolute left-0 right-0 top-full mt-1 z-50 bg-white border border-gray-200 rounded-lg shadow-xl max-h-72 overflow-y-auto"
        >
          {!isFiltering && suggestions.length > 0 && !isLoading && !isError && (
            <div className="px-4 pt-3 pb-1 text-[10px] uppercase font-bold text-gray-400 tracking-wider border-b border-gray-100">
              Popular Cities
            </div>
          )}
          {usingFallback && (
            <div className="px-4 py-2 text-[11px] text-amber-700 bg-amber-50 border-b border-amber-100 flex items-start gap-2">
              <div className="flex-1">
                <div className="font-semibold">Showing offline city list</div>
                <div className="text-amber-600">
                  {error instanceof Error ? error.message : 'Network error'}
                </div>
              </div>
              <button
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault();
                  refetch();
                }}
                className="text-xs underline text-amber-800 hover:text-amber-900 shrink-0"
              >
                Retry
              </button>
            </div>
          )}
          <ul role="listbox">
            {isLoading ? (
              <li className="px-4 py-3 text-sm text-gray-500 flex items-center gap-2">
                <Loader2 size={14} className="animate-spin text-[#D84E55]" />
                Loading cities…
              </li>
            ) : suggestions.length === 0 ? (
              <li className="px-4 py-3 text-sm text-gray-500">
                {value.trim() ? `No matches for "${value}"` : 'No cities available'}
              </li>
            ) : (
              suggestions.map((city, index) => (
                <li
                  key={city}
                  role="option"
                  aria-selected={index === activeIndex}
                  onMouseDown={(e) => {
                    // Use mousedown so the input doesn't blur before we register the click.
                    e.preventDefault();
                    selectCity(city);
                  }}
                  onMouseEnter={() => setActiveIndex(index)}
                  className={`px-4 py-2 cursor-pointer text-sm flex items-center gap-2 ${
                    index === activeIndex ? 'bg-red-50 text-[#D84E55]' : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <MapPin size={14} className="text-gray-400" />
                  <span className="font-medium">{city}</span>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
