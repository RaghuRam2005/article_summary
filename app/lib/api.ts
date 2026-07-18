export const BackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5000';

export type AppUser = {
  id: number;
  name: string;
  email: string;
};

export type HistoryEntry = {
  id: number;
  query: string;
  type: 'keyword' | 'url' | 'content';
  response: string;
  timestamp: string;
};

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BackendUrl}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.error || `Request failed with status ${res.status}`);
  }

  return data as T;
}

// --- Auth ---

export async function signUp(name: string, email: string, password: string): Promise<AppUser> {
  const data = await apiFetch<{ user: AppUser }>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  });
  return data.user;
}

export async function logIn(email: string, password: string): Promise<AppUser> {
  const data = await apiFetch<{ user: AppUser }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  return data.user;
}

export async function logOut(): Promise<void> {
  await apiFetch('/auth/logout', { method: 'POST' });
}

export async function getCurrentUser(): Promise<AppUser | null> {
  try {
    const data = await apiFetch<{ user: AppUser }>('/auth/me', { method: 'GET' });
    return data.user;
  } catch {
    return null;
  }
}

export async function updateDisplayName(name: string): Promise<AppUser> {
  const data = await apiFetch<{ user: AppUser }>('/auth/profile', {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  });
  return data.user;
}

export async function updateUserEmail(newEmail: string, currentPassword: string): Promise<AppUser> {
  const data = await apiFetch<{ user: AppUser }>('/auth/email', {
    method: 'PATCH',
    body: JSON.stringify({ newEmail, currentPassword }),
  });
  return data.user;
}

export async function updateUserPassword(newPassword: string, currentPassword: string): Promise<void> {
  await apiFetch('/auth/password', {
    method: 'PATCH',
    body: JSON.stringify({ newPassword, currentPassword }),
  });
}

// --- History ---

export async function listHistory(): Promise<HistoryEntry[]> {
  const data = await apiFetch<{ history: HistoryEntry[] }>('/history', { method: 'GET' });
  return data.history;
}

export async function createHistory(
  query: string,
  type: HistoryEntry['type'],
  response: string
): Promise<HistoryEntry> {
  const data = await apiFetch<{ item: HistoryEntry }>('/history', {
    method: 'POST',
    body: JSON.stringify({ query, type, response }),
  });
  return data.item;
}

export async function deleteHistoryItem(id: number): Promise<void> {
  await apiFetch(`/history/${id}`, { method: 'DELETE' });
}
