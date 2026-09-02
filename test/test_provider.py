"""Unit tests for SomaFMMediaProvider (network mocked)."""
from unittest.mock import patch

from mediavocab import MediaType, Release, Signals, Work, StreamMode

from ovos_media_provider_somafm import SomaFMMediaProvider


class _FakeStation:
    """Minimal stand-in for radiosoma.SomaFmStation."""

    def __init__(self, title, genre="", description="", dj=""):
        self.title = title
        self.genre = genre
        self.description = description
        self.dj = dj


def _make_release(title):
    work = Work(title=title, media_type=MediaType.RADIO)
    return Release(work=work,
                   uri=f"http://ice.somafm.com/{title}-128-mp3",
                   stream_mode=StreamMode.CONTINUOUS)


def test_instantiation():
    prov = SomaFMMediaProvider()
    assert prov.name == "somafm"


def test_search_accepts_context_kwargs():
    """The provider accepts the pipeline's request-context kwargs."""
    prov = SomaFMMediaProvider()
    stations = [_FakeStation("Groove Salad", genre="ambient")]
    with patch("ovos_media_provider_somafm.get_stations",
               return_value=iter(stations)), \
            patch("ovos_media_provider_somafm.station_to_releases",
                  side_effect=lambda s: [_make_release(s.title)]):
        results = prov.search(
            Signals(medium=MediaType.RADIO, title="groove salad"),
            lang="en-us",
            supported_playback_types={"audio"},
            blocked_genres={"adult"},
            region="US",
            session_id="sess-1",
        )
    assert len(results) == 1
    assert all(isinstance(r, Release) for r in results)


def test_search_filters_by_title_and_returns_releases():
    prov = SomaFMMediaProvider()
    stations = [
        _FakeStation("Groove Salad", genre="ambient|electronica"),
        _FakeStation("Drone Zone", genre="ambient"),
    ]

    def fake_to_releases(station):
        # one Release per encoding -> two per matching station
        return [_make_release(station.title), _make_release(station.title)]

    with patch("ovos_media_provider_somafm.get_stations",
               return_value=iter(stations)) as gs, \
            patch("ovos_media_provider_somafm.station_to_releases",
                  side_effect=fake_to_releases) as s2r:
        results = prov.search(Signals(medium=MediaType.RADIO,
                                      title="groove salad"))

    gs.assert_called_once()
    # only the matching station was converted
    assert s2r.call_count == 1
    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(r, Release) for r in results)
    assert all(r.work.title == "Groove Salad" for r in results)


def test_search_filters_by_genre():
    prov = SomaFMMediaProvider()
    stations = [
        _FakeStation("Groove Salad", genre="ambient|electronica"),
        _FakeStation("Indie Pop Rocks", genre="indie|pop"),
    ]

    with patch("ovos_media_provider_somafm.get_stations",
               return_value=iter(stations)), \
            patch("ovos_media_provider_somafm.station_to_releases",
                  side_effect=lambda s: [_make_release(s.title)]) as s2r:
        results = prov.search(Signals(medium=MediaType.RADIO,
                                      content_genres=["indie"]))

    assert s2r.call_count == 1
    assert len(results) == 1
    assert results[0].work.title == "Indie Pop Rocks"


def test_search_no_query_returns_whole_catalog():
    """A bare RADIO request (no title, no genres) browses the catalog."""
    prov = SomaFMMediaProvider()
    stations = [_FakeStation("A"), _FakeStation("B")]

    with patch("ovos_media_provider_somafm.get_stations",
               return_value=iter(stations)), \
            patch("ovos_media_provider_somafm.station_to_releases",
                  side_effect=lambda s: [_make_release(s.title)]) as s2r:
        results = prov.search(Signals(medium=MediaType.RADIO))

    assert s2r.call_count == 2
    assert {r.work.title for r in results} == {"A", "B"}


def test_search_respects_max_results():
    prov = SomaFMMediaProvider({"max_results": 1})
    stations = [_FakeStation("A"), _FakeStation("B"), _FakeStation("C")]

    with patch("ovos_media_provider_somafm.get_stations",
               return_value=iter(stations)), \
            patch("ovos_media_provider_somafm.station_to_releases",
                  side_effect=lambda s: [_make_release(s.title)]) as s2r:
        results = prov.search(Signals(medium=MediaType.RADIO))

    assert s2r.call_count == 1
    assert len(results) == 1


def test_search_swallows_network_errors():
    prov = SomaFMMediaProvider()
    with patch("ovos_media_provider_somafm.get_stations",
               side_effect=RuntimeError("boom")):
        assert prov.search(Signals(medium=MediaType.RADIO, title="x")) == []


def test_unsupported_typed_query_returns_nothing():
    """A PODCAST/MOVIE-typed query is outside SERVED_MEDIA -> [] without
    even hitting the network."""
    prov = SomaFMMediaProvider()
    stations = [_FakeStation("Groove Salad", genre="ambient")]
    with patch("ovos_media_provider_somafm.get_stations",
               return_value=iter(stations)) as gs, \
            patch("ovos_media_provider_somafm.station_to_releases",
                  side_effect=lambda s: [_make_release(s.title)]):
        assert prov.search(Signals(medium=MediaType.PODCAST)) == []
        assert prov.search(Signals(medium=MediaType.MOVIE, title="x")) == []
    gs.assert_not_called()


def test_music_typed_query_returns_results():
    """SomaFM is music radio: a plain MUSIC request is served too."""
    prov = SomaFMMediaProvider()
    stations = [_FakeStation("Groove Salad", genre="ambient")]
    with patch("ovos_media_provider_somafm.get_stations",
               return_value=iter(stations)), \
            patch("ovos_media_provider_somafm.station_to_releases",
                  side_effect=lambda s: [_make_release(s.title)]):
        results = prov.search(Signals(medium=MediaType.MUSIC))
    assert results
    assert results[0].work.title == "Groove Salad"


def test_generic_medium_browses_catalog():
    prov = SomaFMMediaProvider()
    stations = [_FakeStation("A"), _FakeStation("B")]
    with patch("ovos_media_provider_somafm.get_stations",
               return_value=iter(stations)), \
            patch("ovos_media_provider_somafm.station_to_releases",
                  side_effect=lambda s: [_make_release(s.title)]):
        results = prov.search(Signals(medium=MediaType.GENERIC))
    assert {r.work.title for r in results} == {"A", "B"}
