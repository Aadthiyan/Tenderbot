import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(req: NextRequest) {
  // Read the expected password from the environment setup globally per-tenant
  const APP_PASSWORD = process.env.NEXT_PUBLIC_APP_PASSWORD;

  // We bypass auth entirely during local development if the flag isn't set, 
  // but heavily enforce it when the tenant flag is present in production.
  if (!APP_PASSWORD) {
    return NextResponse.next();
  }

  const basicAuth = req.headers.get('authorization');

  if (basicAuth) {
    const authValue = basicAuth.split(' ')[1];
    const [user, pwd] = atob(authValue).split(':');

    // Only password matters for Single-Tenant basic auth
    if (pwd === APP_PASSWORD) {
      return NextResponse.next();
    }
  }

  // If wrong or missing credentials, reject.
  return new NextResponse('Auth Required', {
    status: 401,
    headers: { 'WWW-Authenticate': 'Basic realm="TenderBot Secured Tenant UI"' },
  });
}

// Ensure the middleware runs on all page routes except static assets and internal APIs
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
