# Optional Camera

The dashboard does not require a camera.

For a USB webcam, install:

```powershell
pip install flask opencv-python
```

Then run:

```powershell
python camera_server.py
```

The server provides:

`http://<PC_IP>:5000/video`

You can later add an `<img src="http://<PC_IP>:5000/video">` panel to the dashboard.

Use a local camera you control.
