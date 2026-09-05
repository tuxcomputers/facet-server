# Linking Local App and Website Identity via Google Auth

## Overview

The desktop app and the website both authenticate users via Google OAuth. This document describes how to link a single person's identity securely across both surfaces, so the desktop app's local SQLite data and the remote API's data both resolve to the same underlying user.

The key idea: Google's ID token contains a `sub` claim, a permanent, unique identifier for that Google account. It stays stable even if the user changes their name or email. Both the desktop app and the website independently authenticate with Google, and as long as the person signs in with the same Google account on both, the backend can map both sessions to the same internal user.

## Flow

1. **Desktop app starts Google OAuth (PKCE)**
   The local app opens the system browser to Google's OAuth consent screen using the Authorization Code flow with PKCE. Use a "Desktop app" type OAuth client in Google Cloud, with a loopback redirect (`http://localhost:PORT/callback`), since desktop apps can't safely embed a client secret.

2. **Google returns tokens to the local app**
   After consent, Google redirects to the loopback listener with an authorization code. The app exchanges this for an ID token (JWT) and access token directly with Google. The ID token's `sub` claim is Google's permanent unique ID for the user.

3. **Local app sends the ID token to the API**
   The raw Google ID token is not used as the app's session credential. Instead, it's POSTed to a backend endpoint (e.g. `/auth/google`), where the server performs the real verification.

4. **Backend verifies the ID token**
   The server verifies the JWT signature against Google's published JWKS, and checks:
   - `aud` matches a known client ID (desktop and web can use different client IDs, both accepted)
   - `iss` is Google
   - `exp` hasn't passed

   A `sub` value is never trusted unless it comes from a signature-verified token.

5. **Backend maps Google sub to an internal user ID**
   An `auth_identities` table (`user_id`, `provider`, `provider_sub`) is looked up by `google_sub`. If a match exists, the internal `user_id` is fetched; otherwise a new user record is created. This internal `user_id` is the durable identity, decoupled from any specific auth provider — adding another provider later (Apple, email/password) just adds another row.

6. **Backend issues its own session tokens**
   The server mints a short-lived access token (JWT, ~15 min) and a longer-lived refresh token, scoped to the internal `user_id`. This — not Google's token — is what the desktop app uses for all further API calls.

7. **Local app stores tokens and internal ID**
   Access/refresh tokens go in the OS keychain (Keychain on macOS, Credential Manager on Windows, Secret Service/libsecret on Linux), not in SQLite. The internal `user_id` is stored in SQLite and used as the foreign key for all locally-cached user data.

8. **All subsequent API calls use the session token**
   The desktop app authenticates to the API with the access token, refreshing via the refresh token when it expires — the same pattern the website's session flow uses.

## Design rationale

- **Server-verified `sub`, never client-asserted.** A client could claim any identity if the server trusted a bare value. Verifying the ID token signature server-side is the actual security boundary.
- **Internal `user_id` as the real key.** Both the desktop SQLite schema and the API's database key off the internal `user_id`, with `google_sub` stored as one linked identity. This avoids restructuring if another auth provider is added later.
- **Google ID tokens are short-lived and single-purpose.** They prove identity at the moment of login, not ongoing API authorization. The backend mints its own tokens for the session.
- **OS keychain over SQLite for secrets.** SQLite files are easy to copy off disk. Access/refresh tokens are the actual keys to the account and belong in the platform's secure credential store.

## Open question

Whether the desktop app should talk to Google directly (as described above), or whether it should route the whole OAuth flow through the backend (the backend does the full Google exchange and hands the desktop app a one-time code to swap for its session token). The second option centralizes all Google-facing OAuth config server-side and keeps the desktop app simpler, at the cost of a bit more backend plumbing.
