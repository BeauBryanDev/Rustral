import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { AuthService } from '../services/auth.service';

/**
 * Global Authentication Store
 * Manages user identity, JWT lifecycle, and hydration from localStorage.
 */
export const useAuthStore = create(
    persist(
        (set, get) => ({
            //STATE
            user: null,
            token: localStorage.getItem('rustral_access_token') || null,
            userId: localStorage.getItem('rustral_user_id') || null,
            isAuthenticated: !!localStorage.getItem('rustral_access_token'),
            isLoading: false,
            error: null,

            // ACTIONS

            /**
             * Orchestrates the login flow: Service Call -> State Update -> LocalStorage
             */
            login: async (email, password) => {
                set({ isLoading: true, error: null });

                try {
                    const data = await AuthService.login(email, password);
                    
                    set({
                        token: data.access_token,
                        userId: data.user_id,
                        isAuthenticated: true,
                        isLoading: false,
                        error: null,
                    });

                    return { success: true };

                } catch (err) {
                    const errorMessage = err.response?.data?.error || 'Authentication Failed';
                    set({ 
                        isLoading: false, 
                        error: errorMessage,
                        isAuthenticated: false 
                    });

                    return { success: false, error: errorMessage };
                }
            },

            /**
             * delete session data and resets the state to initial values.
             */
            logout: () => {
                AuthService.logout();
                set({
                    user: null,
                    token: null,
                    userId: null,
                    isAuthenticated: false,
                    error: null
                });
            },

            /**
             * Updates specific user metadata if needed (e.g., after fetching profile).
             */
            setUser: (userData) => set({ user: userData }),

            /**
             * Computed helper to check if the current session is valid.
             */
            checkSession: () => {
                const token = get().token;
                if (!token) {
                    set({ isAuthenticated: false });
                    return false;
                }
                return true;
            }
        }),
        {
            name: 'rustral-auth-storage', // Unique key in localStorage
            storage: createJSONStorage(() => localStorage),

            partialize: (state) => ({ 
                token: state.token, 
                userId: state.userId, 
                isAuthenticated: state.isAuthenticated 
            }),
        }
    )
);