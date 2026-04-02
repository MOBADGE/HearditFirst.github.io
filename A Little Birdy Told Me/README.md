# A Little Birdy Told Me

Editorial-style breaking news site with four desks:
- `world`
- `tech`
- `health`
- `gaming`

The frontend is static HTML/CSS/JS and reads live data from the Vercel Python function in [`api/briefs.py`](./api/briefs.py).

## Local preview

Use Python's static server from the project root:

```powershell
py -m http.server 8000
```

Then open:

- `http://localhost:8000/`

Note:
- Static page preview works locally this way.
- The Vercel API route (`/api/briefs`) only exists once deployed on Vercel.
- Until then, the frontend falls back to bundled sample data.

## Environment variables

Set these in Vercel Project Settings -> Environment Variables:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
  Default: `gpt-4.1-mini`
- `LOCAL_UTC_OFFSET_HOURS`
  Default: `-6`

If `OPENAI_API_KEY` is missing, the site still works:
- RSS ingestion still runs
- bias-sanitized story cards still render
- desk overviews fall back to deterministic copy instead of AI-generated summaries

## Vercel deployment checklist

1. Import this project into Vercel or connect the repo that contains it.
2. Keep the project root at this folder.
3. Confirm [`vercel.json`](./vercel.json) is included.
4. Add the environment variables from `.env.example`.
5. Deploy a preview build.
6. Verify:
   - `/` loads
   - `/tech.html` loads
   - `/world.html` loads
   - `/health.html` loads
   - `/gaming.html` loads
   - `/api/briefs?category=all` returns JSON
7. After preview looks correct, attach `alittlebirdy.org` to the Vercel project.

## Files to know

- [`index.html`](./index.html): homepage
- [`tech.html`](./tech.html): tech desk
- [`world.html`](./world.html): world desk
- [`health.html`](./health.html): health desk
- [`gaming.html`](./gaming.html): gaming desk
- [`script.js`](./script.js): shared frontend data/render logic
- [`styles.css`](./styles.css): shared visual system
- [`api/briefs.py`](./api/briefs.py): live RSS + sanitizing backend
