# Video ledwall "Installa l'app AREA30"

Genera un MP4 960×1080, 30 fps, ~54 s, senza audio, con QR code verso https://area30.it.

```
pip install pillow "qrcode[pil]"      # serve anche ffmpeg installato
python strumenti/video/genera.py video-ledwall-area30-app.mp4
python strumenti/video/genera.py x anteprime   # solo fotogrammi di prova in strumenti/video/anteprime
```

Testi, durate e scene sono nella lista `SCENE` in fondo a `genera.py`.
