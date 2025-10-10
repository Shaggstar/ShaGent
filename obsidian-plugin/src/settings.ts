export interface BetterSelfSettings {
  supabaseUrl: string;
  supabaseKey: string;
  webAppUrl: string;
}

export const DEFAULT_SETTINGS: BetterSelfSettings = {
  supabaseUrl: '',
  supabaseKey: '',
  webAppUrl: 'http://localhost:3000',
};
