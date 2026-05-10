import './globals.css'
import { Inter } from 'next/font/google'
import { Toaster } from 'react-hot-toast'
import Providers from '@/components/Providers'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <nav className="bg-red-500 text-white p-4 shadow-md">
            <div className="max-w-7xl mx-auto flex justify-between items-center">
              <div className="flex items-center space-x-8">
                <Link href="/" className="text-white hover:text-red-100 font-semibold text-lg">
                  RedBus
                </Link>
                <Link href="/" className="text-white hover:text-red-100 ml-4">
                  🏠 Home
                </Link>
                <Link href="/search" className="text-white hover:text-red-100">
                  Search Trips
                </Link>
                <Link href="/bookings" className="text-white hover:text-red-100">
                  My Bookings
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <Link href="/login" className="text-white hover:text-red-100">
                  Login
                </Link>
              </div>
            </div>
          </nav>
          <div className="min-h-screen bg-background">
            {children}
          </div>
          <Toaster position="top-center" />
        </Providers>
      </body>
    </html>
  )
}