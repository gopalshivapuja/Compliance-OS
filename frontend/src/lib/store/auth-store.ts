/**
 * Authentication store using Zustand
 *
 * Manages auth state with localStorage persistence for client-side
 * and cookie sync for server-side middleware access.
 */
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface User {
  user_id: string
  tenant_id: string
  email: string
  full_name: string
  roles: string[]
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  login: (accessToken: string, refreshToken: string, user: User) => void
  logout: () => void
  updateUser: (user: User) => void
  updateTokens: (accessToken: string, refreshToken: string) => void
}

/**
 * Set a cookie for middleware access
 * Uses SameSite=Lax for security while allowing navigation
 */
function setCookie(name: string, value: string, days: number = 7) {
  if (typeof document === 'undefined') return
  const expires = new Date()
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000)
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`
}

/**
 * Remove a cookie
 */
function removeCookie(name: string) {
  if (typeof document === 'undefined') return
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;SameSite=Lax`
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: (accessToken, refreshToken, user) => {
        // Sync token to cookie for middleware access
        setCookie('accessToken', accessToken)
        set({
          accessToken,
          refreshToken,
          user,
          isAuthenticated: true,
        })
      },

      logout: () => {
        // Clear cookie on logout
        removeCookie('accessToken')
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },

      updateUser: (user) => set({ user }),

      updateTokens: (accessToken, refreshToken) => {
        // Sync new token to cookie on refresh
        setCookie('accessToken', accessToken)
        set({ accessToken, refreshToken })
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)
