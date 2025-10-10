import { createClient, SupabaseClient } from '@supabase/supabase-js';

export const initSupabaseClient = (supabaseUrl: string, supabaseKey: string): SupabaseClient => {
  return createClient(supabaseUrl, supabaseKey);
};
