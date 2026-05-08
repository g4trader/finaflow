import { createClient } from '@supabase/supabase-js'

// Use this helper only on server-side (API routes). Requires SUPABASE_SERVICE_ROLE_KEY in env.
const url = process.env.SUPABASE_URL as string
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY as string

if (!url || !serviceKey) {
  console.warn('Supabase server helper missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
}

export function createSupabaseServer() {
  if (!url || !serviceKey) {
    throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
  }

  return createClient(url, serviceKey)
}
