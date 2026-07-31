# ovos-media-provider-somafm

OVOS **MediaProvider** plugin for [SomaFM](https://somafm.com). It replaces
the deprecated OCP search skill
[`ovos-skill-somafm`](https://github.com/OpenVoiceOS/ovos-skill-somafm).

Instead of broadcasting `ovos.common_play.query` over the bus and waiting for
skills to answer, the OCP pipeline loads MediaProvider plugins in-process,
gates them by routing, and calls `search()` directly. This plugin wraps the
[`radiosoma`](https://github.com/TigreGotico/radiosoma) client. Its
`converters.station_to_releases` function maps each SomaFM channel into
[`mediavocab.Release`](https://github.com/TigreGotico/mediavocab) objects, one
per stream encoding.

SomaFM is a fixed, curated channel list, so `search()` is a local filter over
the station catalog. It matches `signals.title` against the channel name and
description, and `signals.content_genres` against the channel genre tags.

## Install

```bash
pip install ovos-media-provider-somafm
```

## Usage

The OCP pipeline discovers and loads this plugin through its entry point. To
call it directly:

```python
from mediavocab import Signals
from ovos_media_provider_somafm import SomaFMMediaProvider

provider = SomaFMMediaProvider()
releases = provider.search(Signals(title="deep space"))
```

A query with neither `title` nor `content_genres` set matches every station,
so a bare `RADIO` request browses the whole catalog.

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

## Related projects

- [`ovos-plugin-manager`](https://github.com/OpenVoiceOS/ovos-plugin-manager): defines the `MediaProvider` template this plugin implements.
- [`radiosoma`](https://github.com/TigreGotico/radiosoma): the SomaFM API client this plugin wraps.
- [`mediavocab`](https://github.com/TigreGotico/mediavocab): the `Release`/`Signals` vocabulary used to describe search queries and results.
- [`ovos-skill-somafm`](https://github.com/OpenVoiceOS/ovos-skill-somafm): the deprecated OCP search skill this plugin replaces.

## License

Apache-2.0
