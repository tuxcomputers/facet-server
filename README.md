# facet-server

The multi-user sync and reporting backend for **Facet**, the macOS time tracking app that runs off a
TimeFlip2 cube ([Facet app](https://github.com/tuxcomputers/TimeFlipApp)).

Facet today is one person on one Mac, recording into a local SQLite database. That is the whole of
it: there is no account, no server, and no way for two people using it to see each other's time.
This repo is what changes that. Each person keeps recording exactly as they do now, the app posts
each entry to this API as it is recorded, and a team leader reports across everybody from one place.

**Nothing is built yet.** The repo holds design notes and this README. No stack has been chosen, no
API surface is fixed, and everything below is the intended shape rather than a description of
running code.

## What is here

| Path | What it is |
| --- | --- |
| `docs/google-auth-linking.md` | How one person's desktop app and website sessions resolve to a single internal user, via a server-verified Google `sub`. |

## What it is for

- **Sync.** The desktop app posts a time entry to this API as the entry is created, so the server
  holds the team's recorded time without anybody exporting or uploading anything by hand.
- **Reporting for a team leader.** Group by person to see what each member has been working on, or
  group by task to see how much time the whole team spent on it.

The local database stays the source of truth for that person's own machine. Sync is additive: the
app has to keep working with no network and no account, because that is what it does now, and a
cube on a desk with no internet is a normal way to use it.

## Sync, and the part that sync on creation does not cover

Posting on creation is the trigger, not the guarantee. An entry recorded while the machine is
offline, or while the server is down, is never created again, so it needs a way to go across later.

The app already solves this exact problem once, for Google Calendar, and it is worth copying rather
than re-deriving: recording an entry **sweeps everything not yet synced**, so time recorded offline
goes across on the next entry, and each one is **read back and confirmed** before the entry is
marked done. The same three pieces apply here:

1. A per-entry "synced" flag in the app's local database, the way `synced_to_google_calendar`
   already sits on `time_entry`.
2. On each record, post the new entry and every unsynced one behind it.
3. Mark an entry synced only once the server confirms it holds it, not when the request returns.

**Re-posting has to be safe.** A request that times out after the server committed it will be sent
again, and a retry must not produce a second row. The app's `time_entry_id` is only unique within
one machine's database, so the server cannot key on it alone: the identity of an entry is the user
plus a client-side key, either the local id scoped to the user or a UUID the app generates when it
writes the row.

## Identity

Both the desktop app and the website authenticate with Google, and the same Google account on both
resolves to one internal `user_id`. The server verifies the ID token's signature against Google's
JWKS and only then trusts the `sub` claim, maps that to an internal user, and mints its own session
tokens. Google's token proves who somebody is at the moment of login; it is not the API credential.

[`docs/google-auth-linking.md`](docs/google-auth-linking.md) is the full flow and the reasoning.

## Reporting, and three things the app's data does not hand over for free

Each of these is a decision this server has to make, and each one is cheaper to settle now than
after a schema exists.

**A task is not yet a shared thing.** In the app a category belongs to one person's database and is
unique by name only within it, so two people typing "Meeting" have two unrelated categories that
happen to match as strings. There is a `project` table, but nothing in the app reads or writes it
yet. Reporting by task across a team needs a task identity the server owns, with each person's local
categories mapped onto it. Matching on names is the version that looks fine in a demo and produces
wrong totals the first time somebody types "meetings".

**Times are local, and carry their zone.** Every date/time column in the app stores local time
rather than UTC, and `time_entry` carries a `start_timezone_id` and an `end_timezone_id` against a
table of IANA zone names. The zone has to travel with the entry, or the server cannot put two
people's days on one axis.

**A day does not start at midnight.** `daily_reset_time` is a per-person setting, so "Tuesday" is a
different span for two people who set it differently. Absolute spans are unambiguous and should be
what a cross-team report uses; a person's own reset time makes sense only where that person is the
grouping.

## Not decided yet

- Language, framework, database and where it runs.
- Whether the desktop app talks to Google directly or routes the whole OAuth flow through this
  backend (the open question at the end of the auth doc).
- Whether an entry can be edited or deleted after it has synced. The app cannot yet correct a
  recorded entry at all, so the API could start append-only, but the answer decides whether entries
  need versions.
- What a "team" is: how somebody joins one, who may report across it, and whether a person can be in
  more than one.

## Related repositories

| Repo | What it is |
| --- | --- |
| [TimeFlipApp](https://github.com/tuxcomputers/TimeFlipApp) | Facet itself, the macOS menu bar app and its local SQLite database. |
| [facet_tux_com_au](https://github.com/tuxcomputers/facet_tux_com_au) | The public pages at facet.tux.com.au: homepage, privacy policy, terms. |
| facet-server | This repo. |
