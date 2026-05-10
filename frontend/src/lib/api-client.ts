import axios from 'axios';

// API Types based on backend schemas
export interface Trip {
  id: number;
  bus_name: string;
  departure_time: string;
  arrival_time: string;
  available_seats: number;
  price: number;
}

export interface TripSearchRequest {
  source: string;
  destination: string;
  travel_date: string;
  bus_types?: string[];
  min_price?: number;
  max_price?: number;
  departure_window?: 'morning' | 'afternoon' | 'evening' | 'night';
  sort_by?: 'price_asc' | 'price_desc' | 'earliest' | 'latest';
}

export interface BookingRequest {
  trip_id: number;
  seat_ids: number[];
}

export interface BookingResponse {
  bookings: Array<{
    id: number;
    user_id: number;
    trip_id: number;
    seat_id: number;
    status: 'PENDING' | 'CONFIRMED' | 'CANCELLED';
    total_price?: number;
    booking_date: string;
  }>;
  total_seats: number;
  message: string;
}

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8001/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add authentication token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Request interceptor for rate limiting
api.interceptors.response.use(
  (response) => {
    const rateLimitRemaining = response.headers['x-ratelimit-remaining'];
    const rateLimitReset = response.headers['x-ratelimit-reset'];
    
    if (rateLimitRemaining !== undefined) {
      console.log(`Rate limit remaining: ${rateLimitRemaining}`);
    }
    
    return response;
  },
  (error) => {
    // Handle rate limiting errors
    if (error.response?.status === 429) {
      console.error('Rate limit exceeded:', error.response.data);
      // Could trigger a toast here
    }
    
    return Promise.reject(error);
  }
);

// API Functions
export const tripApi = {
  search: async (params: TripSearchRequest): Promise<Trip[]> => {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => queryParams.append(key, v));
        } else {
          queryParams.append(key, value.toString());
        }
      }
    });
    
    const response = await api.get(`/trips/search?${queryParams.toString()}`);
    return response.data;
  },
  
  getTripSeats: async (tripId: number): Promise<any> => {
    const response = await api.get(`/trips/${tripId}/seats`);
    return response.data;
  },
};

export const bookingApi = {
  create: async (data: BookingRequest): Promise<BookingResponse> => {
    const response = await api.post('/bookings/', data);
    return response.data;
  },

  createBooking: async (tripId: number, seatNumbers: string[], totalAmount: number): Promise<any> => {
    const response = await api.post('/bookings/', {
      trip_id: tripId,
      seat_numbers: seatNumbers,
      total_amount: totalAmount
    });
    return response.data;
  },
  
  getMyBookings: async (): Promise<any[]> => {
    const response = await api.get('/bookings/me');
    return response.data;
  },
  
  getBooking: async (bookingId: number): Promise<any> => {
    const response = await api.get(`/bookings/${bookingId}`);
    return response.data;
  },
};

export const busApi = {
  getAll: async (): Promise<any[]> => {
    const response = await api.get('/buses/');
    return response.data;
  },
};

export const routeApi = {
  getAll: async (): Promise<any[]> => {
    const response = await api.get('/routes/');
    return response.data;
  },
  search: async (source: string, destination: string, date: string): Promise<any> => {
    const response = await api.get(`/routes/search?source=${source}&destination=${destination}&date=${date}`);
    return response.data;
  },
};

export const locationApi = {
  getAll: async (): Promise<string[]> => {
    const response = await api.get('/trips/locations');
    return response.data;
  },
};

export const authApi = {
  login: async (email: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    
    const response = await api.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data;
  },
  
  register: async (email: string, password: string): Promise<any> => {
    const response = await api.post('/auth/register', {
      email: email,
      password: password
    });
    return response.data;
  },
  
  logout: async (): Promise<void> => {
    const response = await api.post('/auth/logout');
    return response.data;
  },
};

export default api;
