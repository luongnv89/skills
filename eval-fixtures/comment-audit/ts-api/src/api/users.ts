// Users endpoint handlers.

export interface User {
  id: string;
  name: string;
}

// The upstream API caps pages at 100 items and rejects larger requests
// with a 400, so never ask for more than that.
const PAGE_SIZE = 100;

export async function listUsers(fetchPage: (size: number) => Promise<User[]>): Promise<User[]> {
  // TODO: follow the next-page cursor; only the first page is read today.
  return fetchPage(PAGE_SIZE);
}

export function role(code: number): string {
  switch (code) {
    case 0:
      code = 1;
      // falls through
    case 1:
      return "member";
    default:
      return "guest";
  }
}

export function parse(raw: string): User | null {
  try {
    return JSON.parse(raw) as User;
  } catch {
    // ignore malformed bodies
  }
  return null;
}

// @ts-expect-error legacy callers still pass a number id
export const legacy: User = { id: 7, name: "x" };

// return the user's name
export const nameOf = (u: User): string => u.name; // the name field
