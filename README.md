# ovos-media-provider-somafm

OVOS **MediaProvider** plugin for [SomaFM](https://somafm.com). Replaces the
deprecated OCP search skill
[`ovos-skill-somafm`](https://github.com/OpenVoiceOS/ovos-skill-somafm).

Instead of broadcasting `ovos.common_play.query` over the bus and waiting for
skills to answer, the OCP pipeline loads MediaProvider plugins in-process, gates
them by routing, and calls `search()` directly. This plugin wraps the
[`radiosoma`](https://github.com/TigreGotico/radiosoma) client, whose
`converters.station_to_releases` maps each SomaFM channel into
[`mediavocab.Release`](https://github.com/TigreGotico/mediavocab) objects (one
per stream encoding).

SomaFM is a fixed, curated channel list, so `search()` is a local filter over
the station catalog matching `signals.title` against channel name/description
and `signals.content_genres` against the channel genre tags.

## Install

```bash
pip install ovos-media-provider-somafm
```

## Routing

| Axis | Value |
|------|-------|
| `media` | `RADIO` |
| `playback_type` | `AUDIO` |
| `genre_filter` | *(none)* |

## Entry point

```toml
[project.entry-points."opm.media.provider"]
somafm = "ovos_media_provider_somafm:SomaFMMediaProvider"
```

## Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `max_results` | `10` | Maximum number of matching channels returned per search. |

## License

Apache-2.0
