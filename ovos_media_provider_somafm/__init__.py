"""SomaFM MediaProvider plugin for OVOS.

Wraps the :mod:`radiosoma` client and exposes SomaFM's internet-radio catalog to
the OCP pipeline as a
:class:`~ovos_plugin_manager.templates.media_provider.MediaProvider`. Replaces
the deprecated OCP search skill ``ovos-skill-somafm``.

SomaFM is a fixed, finite list of curated channels served from a single
``channels.xml`` feed. ``radiosoma.get_stations`` returns the whole list, and
``radiosoma.converters.station_to_releases`` maps each channel into one
:class:`mediavocab.Release` per stream encoding (per mediavocab axiom 8 each
distinct codec/bitrate is a separate ``Release`` of the same ``Work``). Search
is therefore a local filter over the station list — no per-query network search
endpoint exists — matching ``signals.title`` against channel name/description
and ``signals.content_genres`` against the channel genre tags.
"""
from typing import ClassVar, List, Optional, Set

from ovos_utils.log import LOG

from mediavocab import MediaType, Release, Signals

from ovos_plugin_manager.templates.media_provider import MediaProvider

from radiosoma import get_stations
from radiosoma.converters import station_to_releases

from ovos_media_provider_somafm.version import __version__  # noqa: F401


class SomaFMMediaProvider(MediaProvider):
    """Search the SomaFM channel catalog and return playable radio releases."""

    name: ClassVar[str] = "somafm"

    # SomaFM is internet music radio: every Release it builds carries
    # work.media_type == RADIO, and it legitimately answers plain MUSIC
    # requests too (it *is* the music being played).
    SERVED_MEDIA: ClassVar[Set[MediaType]] = {MediaType.RADIO, MediaType.MUSIC}

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        # max channels to return per search, overridable via plugin config
        self.max_results: int = int(self.config.get("max_results", 10))

    @staticmethod
    def _station_matches(station, title: str, genres: List[str]) -> bool:
        """A station matches when its name/description contains the query
        title, or when any requested genre tag is present in the station's
        genres. A query with neither title nor genres matches everything (a
        bare ``RADIO`` request → browse the whole catalog)."""
        if not title and not genres:
            return True

        if title:
            haystack = " ".join(
                p for p in (station.title, station.description, station.dj) if p
            ).lower()
            if title in haystack:
                return True

        if genres:
            station_genres = (station.genre or "").lower()
            if any(g and g.lower() in station_genres for g in genres):
                return True

        return False

    def search(self, signals: Signals, lang: str = "en-us", *,
               supported_playback_types: Optional[Set[str]] = None,
               blocked_genres: Optional[Set[str]] = None,
               region: Optional[str] = None,
               session_id: Optional[str] = None) -> List[Release]:
        """Filter the SomaFM catalog by ``signals.title`` /
        ``signals.content_genres`` and return one :class:`Release` per stream
        encoding of each matching channel.

        SomaFM has no per-query search endpoint; the full station list is
        fetched (and cached by radiosoma's session) then filtered locally.

        A query naming a concrete media type outside ``SERVED_MEDIA`` (e.g.
        MOVIE, PODCAST) cannot be served by this provider and returns ``[]``
        — a query with no type (GENERIC/unset) may still legitimately browse
        the catalog.
        """
        medium = signals.medium
        if medium is not None and medium not in (MediaType.GENERIC,) \
                and medium not in self.SERVED_MEDIA:
            return []

        title = (signals.title or "").strip().lower()
        genres = [g for g in (signals.content_genres or []) if g]

        releases: List[Release] = []
        try:
            matched = 0
            for station in get_stations():
                if not self._station_matches(station, title, genres):
                    continue
                try:
                    releases.extend(station_to_releases(station))
                except Exception:
                    LOG.exception(
                        f"Failed to convert SomaFM station to Release: "
                        f"{station!r}"
                    )
                matched += 1
                if matched >= self.max_results:
                    break
        except Exception:
            LOG.exception("SomaFM search failed")
            return []
        return releases
