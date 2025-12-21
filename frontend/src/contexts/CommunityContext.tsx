/**
 * Community Context - Multi-community support
 *
 * Manages current community selection and provides community functions to the app.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

interface Community {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  settings: Record<string, any>;
  is_public: boolean;
}

interface CommunityContextType {
  currentCommunity: Community | null;
  communities: Community[];
  loading: boolean;
  selectCommunity: (communityId: string) => void;
  refreshCommunities: () => Promise<void>;
  createCommunity: (name: string, description?: string) => Promise<Community>;
}

const CommunityContext = createContext<CommunityContextType | undefined>(undefined);

const COMMUNITY_KEY = 'solarpunk_current_community';

export function CommunityProvider({ children }: { children: React.ReactNode }) {
  const [currentCommunity, setCurrentCommunity] = useState<Community | null>(null);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [loading, setLoading] = useState(true);

  // Load communities on mount
  useEffect(() => {
    loadCommunities();
  }, []);

  const loadCommunities = async () => {
    try {
      // Fetch public communities (no auth required)
      const response = await axios.get('/api/vf/communities/public');
      const userCommunities: Community[] = response.data;

      setCommunities(userCommunities);

      // Try to restore previously selected community
      const storedCommunityId = localStorage.getItem(COMMUNITY_KEY);
      if (storedCommunityId) {
        const community = userCommunities.find(c => c.id === storedCommunityId);
        if (community) {
          setCurrentCommunity(community);
        } else if (userCommunities.length > 0) {
          // Stored community not found, select first available
          setCurrentCommunity(userCommunities[0]);
          localStorage.setItem(COMMUNITY_KEY, userCommunities[0].id);
        }
      } else if (userCommunities.length > 0) {
        // No stored community, select first available
        setCurrentCommunity(userCommunities[0]);
        localStorage.setItem(COMMUNITY_KEY, userCommunities[0].id);
      }
    } catch (error) {
      console.error('Failed to load communities:', error);
      // Create a default community if none exist
      const defaultCommunity: Community = {
        id: 'default-community',
        name: 'Local Community',
        description: 'Default local community',
        created_at: new Date().toISOString(),
        member_count: 1,
        is_public: true
      };
      setCommunities([defaultCommunity]);
      setCurrentCommunity(defaultCommunity);
    } finally {
      setLoading(false);
    }
  };

  const selectCommunity = (communityId: string) => {
    const community = communities.find(c => c.id === communityId);
    if (community) {
      setCurrentCommunity(community);
      localStorage.setItem(COMMUNITY_KEY, communityId);
    }
  };

  const refreshCommunities = async () => {
    setLoading(true);
    await loadCommunities();
  };

  const createCommunity = async (name: string, description?: string): Promise<Community> => {
    try {
      const response = await axios.post('/api/vf/communities', {
        name,
        description,
        is_public: true
      });

      const newCommunity: Community = response.data;

      // Add to communities list
      setCommunities(prev => [...prev, newCommunity]);

      // Auto-select newly created community
      setCurrentCommunity(newCommunity);
      localStorage.setItem(COMMUNITY_KEY, newCommunity.id);

      return newCommunity;
    } catch (error) {
      console.error('Failed to create community:', error);
      throw error;
    }
  };

  const value: CommunityContextType = {
    currentCommunity,
    communities,
    loading,
    selectCommunity,
    refreshCommunities,
    createCommunity,
  };

  return <CommunityContext.Provider value={value}>{children}</CommunityContext.Provider>;
}

export function useCommunity() {
  const context = useContext(CommunityContext);
  if (context === undefined) {
    throw new Error('useCommunity must be used within a CommunityProvider');
  }
  return context;
}
