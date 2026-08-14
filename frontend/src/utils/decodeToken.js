// A JWT is three base64 parts separated by dots (header.payload.signature).
// The middle part carries sub, email, and roles, this pulls just that part
// out and parses it, no extra library needed.
export function decodeToken(token) {
  if (!token) return null;

  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
}