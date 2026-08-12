from types import SimpleNamespace

from PIL import Image, ImageChops

from scripts.poster_assets import fetch_title_logos as title_logos


def test_title_logo_fetch_copies_repository_local_source(tmp_path, monkeypatch):
    source = tmp_path / "images" / "logos" / "promo" / "default.png"
    source.parent.mkdir(parents=True)
    Image.new("RGBA", (64, 32), (255, 204, 0, 255)).save(source)

    asset_dir = tmp_path / "poster"
    source_dir = tmp_path / "poster-workspace" / "sources"
    bundle = SimpleNamespace(
        asset_dir=asset_dir,
        source_dir=source_dir,
        manifest_path=asset_dir / "poster.yaml",
        manifest={
            "title_logo": {"files": {"de": "logos/logo-de.png"}}
        },
    )
    monkeypatch.setattr(title_logos, "ROOT", tmp_path)
    monkeypatch.setattr(title_logos, "POSTER_ASSETS", tmp_path)
    monkeypatch.setattr(
        title_logos,
        "poster_bundle",
        lambda *_args, **_kwargs: bundle,
    )
    monkeypatch.setattr(
        title_logos,
        "load_poster_scope_data",
        lambda *_args, **_kwargs: {
            "logo_urls": {"de": "images/logos/promo/default.png"}
        },
    )

    written = title_logos.fetch_title_logos("SVP")

    assert written == [source_dir / "logos" / "logo-de.png"]
    with Image.open(written[0]) as copied, Image.open(source) as original:
        assert copied.mode == "RGBA"
        assert copied.size == original.size
        assert ImageChops.difference(copied, original).getbbox() is None
