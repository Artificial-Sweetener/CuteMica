"""Verify worker completion remains quiet after Qt begins application shutdown."""

from pathlib import Path

from PIL import Image
from PySide6.QtCore import QCoreApplication, QEvent

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.recipe import ResolvedMicaAltStyle
from cutemica.scheduler import MaterialJob, MaterialRequest


def test_material_job_tolerates_deleted_signal_owner(tmp_path: Path) -> None:
    wallpaper_path = tmp_path / "wallpaper.png"
    Image.new("RGB", (20, 20), (10, 20, 30)).save(wallpaper_path)
    geometry = Rect(0, 0, 20, 20)
    binding = ScreenBinding("screen", geometry, "screen", geometry, 1.0)
    request = MaterialRequest(
        generation=1,
        cache_key="key",
        wallpaper_path=wallpaper_path,
        placement=WallpaperPlacement.FILL,
        background_color=(0, 0, 0),
        neighbor_halo=True,
        binding=binding,
        all_bindings=(binding,),
        texture_scale=0.5,
        style=ResolvedMicaAltStyle(
            material_color=(255, 255, 255),
            tint_opacity=0.8,
            luminosity_opacity=1.0,
            blur_radius_dip=1.0,
            fallback_color=(255, 255, 255),
        ),
    )
    job = MaterialJob(request)
    job.signals.deleteLater()
    QCoreApplication.sendPostedEvents(job.signals, QEvent.Type.DeferredDelete)

    job.run()
