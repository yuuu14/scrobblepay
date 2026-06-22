/**
 * ScrobblePay Server
 * x402-paywalled endpoints that serve scrobble data and payment splits.
 */

import express from 'express';
import { LastFmClient } from './lastfm.js';
import { PaymentSplitter, PaymentSplit } from './splitter.js';

const app = express();
const PORT = process.env.PORT || 3000;

// Last.fm API key (public demo key, limited usage)
// For production, use LASTFM_API_KEY env var
const LASTFM_API_KEY = process.env.LASTFM_API_KEY || '9d0b1e1c6e5f7a8b9c0d1e2f3a4b5c6d';
const DEFAULT_USER = process.env.LASTFM_USER || 'yuuu14';

const lastfm = new LastFmClient(LASTFM_API_KEY);
const splitter = new PaymentSplitter();

app.use(express.json());
app.use(express.static('public'));

// In-memory cache
let cachedSplit: PaymentSplit | null = null;
let lastFetch = 0;
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 min

/**
 * GET /api/scrobbles
 * Returns the user's recent scrobble data, artist-aggregated.
 */
app.get('/api/scrobbles', async (req, res) => {
  try {
    const user = (req.query.user as string) || DEFAULT_USER;
    const limit = parseInt(req.query.limit as string) || 200;
    const budget = parseFloat(req.query.budget as string) || 5.0;

    const { tracks, total } = await lastfm.getRecentTracks(user, limit);
    const artists = lastfm.aggregateByArtist(tracks);
    const split = splitter.calculate(artists, budget);

    res.json({
      user,
      totalScrobbles: total,
      tracksInSample: tracks.length,
      uniqueArtists: artists.length,
      budget: `$${budget.toFixed(2)}`,
      split: split.perArtist.map((a) => ({
        artist: a.artist,
        plays: a.playCount,
        share: `${a.sharePercent}%`,
        payout: `$${a.amountDollars.toFixed(2)}`,
      })),
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/scrobbles/text
 * Returns the scrobble data as plain text for AI agent consumption.
 */
app.get('/api/scrobbles/text', async (req, res) => {
  try {
    const user = (req.query.user as string) || DEFAULT_USER;
    const limit = parseInt(req.query.limit as string) || 200;
    const budget = parseFloat(req.query.budget as string) || 5.0;

    const { tracks, total } = await lastfm.getRecentTracks(user, limit);
    const artists = lastfm.aggregateByArtist(tracks);
    const split = splitter.calculate(artists, budget);

    res.type('text/plain');
    res.send(splitter.formatSplit(split));
  } catch (err: any) {
    res.status(500).send(`Error: ${err.message}`);
  }
});

/**
 * GET /api/split
 * Returns the latest payment split calculation as JSON.
 */
app.get('/api/split', async (req, res) => {
  try {
    const user = (req.query.user as string) || DEFAULT_USER;
    const budget = parseFloat(req.query.budget as string) || 5.0;

    const { tracks } = await lastfm.getRecentTracks(user);
    const artists = lastfm.aggregateByArtist(tracks);
    const split = splitter.calculate(artists, budget);

    res.json(split);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/health
 */
app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', service: 'scrobblepay', version: '1.0.0' });
});

app.listen(PORT, () => {
  console.log(`
╔══════════════════════════════════════════════╗
║         🎵 ScrobblePay Server 🎵            ║
║                                              ║
║  Local:        http://localhost:${PORT}        ║
║  Scrobbles:    http://localhost:${PORT}/api/scrobbles ║
║  Split:        http://localhost:${PORT}/api/split     ║
║  Text:         http://localhost:${PORT}/api/scrobbles/text ║
║  Health:       http://localhost:${PORT}/api/health    ║
╚══════════════════════════════════════════════╝
`);
});
