/**
 * Last.fm API client for fetching scrobble data.
 * Uses the public Last.fm API (no auth needed for read-only user data).
 */

const LASTFM_API = 'https://ws.audioscrobbler.com/2.0/';

export interface Scrobble {
  artist: string;
  track: string;
  album: string;
  timestamp: number;
  url: string;
}

export interface ArtistSummary {
  name: string;
  playCount: number;
  mbid?: string;
  url: string;
}

interface LastFmTrack {
  artist: { '#text': string; mbid?: string };
  name: string;
  album: { '#text': string; mbid?: string };
  url: string;
  date?: { uts: string };
  '@attr'?: { nowplaying: string };
}

export class LastFmClient {
  constructor(private apiKey: string) {}

  /**
   * Fetch recent scrobbles for a user
   */
  async getRecentTracks(
    user: string,
    limit = 200,
    page = 1
  ): Promise<{ tracks: Scrobble[]; total: number }> {
    const params = new URLSearchParams({
      method: 'user.getRecentTracks',
      user,
      api_key: this.apiKey,
      format: 'json',
      limit: String(limit),
      page: String(page),
    });

    const res = await fetch(`${LASTFM_API}?${params}`);
    const data = (await res.json()) as any;

    if (data.error) {
      throw new Error(`Last.fm API error: ${data.message}`);
    }

    const tracks: Scrobble[] = (data.recenttracks?.track || [])
      .filter((t: LastFmTrack) => !t['@attr']?.nowplaying) // skip currently playing
      .map((t: LastFmTrack) => ({
        artist: t.artist['#text'],
        track: t.name,
        album: t.album['#text'],
        timestamp: parseInt(t.date?.uts || '0', 10),
        url: t.url,
      }));

    return {
      tracks,
      total: parseInt(data.recenttracks?.['@attr']?.total || '0', 10),
    };
  }

  /**
   * Aggregate scrobbles by artist with play counts
   */
  aggregateByArtist(tracks: Scrobble[]): ArtistSummary[] {
    const map = new Map<string, { name: string; count: number; url: string }>();

    for (const t of tracks) {
      const key = t.artist.toLowerCase();
      const existing = map.get(key);
      if (existing) {
        existing.count++;
      } else {
        map.set(key, {
          name: t.artist,
          count: 1,
          url: `https://www.last.fm/music/${encodeURIComponent(t.artist)}`,
        });
      }
    }

    return Array.from(map.values())
      .map((a) => ({ name: a.name, playCount: a.count, url: a.url }))
      .sort((a, b) => b.playCount - a.playCount);
  }
}
