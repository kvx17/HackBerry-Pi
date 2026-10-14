# Generic Adapter **USB JL-HVC01A**  (USB3.0 Capture at `/dev/videoX`)

You can change settings manually or append the command

The working settings are:

- **Chroma**: `MJPG`

- **Resolution**: `1920x1080`

- **Frame rate**: `30`

- **Aspect ratio**: `16:9


Key limits from the specs:
- Maximum **output** (what your Linux machine receives): **1920×1080 @ 30 Hz**
- It can accept higher input (up to 4K@30) but downscales to 1080p30
- UVC + UAC compliant → shows up as a normal `/dev/videoX` device on Arch (no special drivers needed)
- Appears as “Capture FHD” on Windows

These cheap devices almost always deliver usable 1080p30 only via **MJPG** (Motion-JPEG). Uncompressed YUYV/YUY2 at 1080p is usually limited to very low frame rates (often ~5 fps) because of USB bandwidth.

#### Recommended VLC configuration for this adapter

1. **Check what the device actually exposes** (do this first):
   ```bash
   v4l2-ctl --list-devices
   v4l2-ctl -d /dev/videoX --list-formats-ext
   ```
   Look for the highest resolution + frame rate combination under `MJPG`.

2. **In VLC → Media → Open Capture Device…**
   - Video device name: your `/dev/videoX`
   - Click **Advanced options**:
     - **Video size**: `1920x1080`
     - **Picture aspect-ratio**: `16:9`
     - **Video input frame rate**: `30`
     - **Video input chroma format**: `MJPG` (this is the important one for this model)
   - Check **Show more options** and you can also append:
     ```
     :chroma=MJPG :width=1920 :height=1080 :fps=30
     ```
   - Set Caching low (0–100 ms) if you want lower latency.

3. **Video standard**: Leave it empty / default.  
   It is irrelevant for this UVC HDMI device (no analog NTSC/PAL).

4. **Change the video output module** (very common fix for softness/pixelation):
   - Tools → Preferences → Video
   - Set **Output** to **XVideo output (XCB)** (or try **X11 video output**)
   - Save and fully restart VLC

## I reccomend this option the most
#### Quick command-line alternative
```bash
vlc v4l2:///dev/videoX:chroma=MJPG:width=1920:height=1080:fps=30
```

#### Additional tips for this device
- Plug it into a USB 3.x port (blue) even though the device itself is often bandwidth-limited.
- The source PC should output 1080p (or the capture card will downscale, which softens the image further).
- If the image is still soft after the above, test the same device in OBS (Video Capture Device → Custom → 1920x1080, 30 fps, MJPG or YUY2). If OBS looks sharper, the remaining issue is VLC’s rendering path.
- You can also try forcing the format system-wide before opening VLC:
  ```bash
  v4l2-ctl -d /dev/videoX --set-fmt-video=width=1920,height=1080,pixelformat=MJPG