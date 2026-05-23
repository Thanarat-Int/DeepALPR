"""Frame source -- abstracts a video file or an RTSP camera stream.

The same class handles both: pass a file path or an `rtsp://...` URL. This is
where a production system would plug in real CCTV cameras.
"""
import cv2


class FrameSource:
    def __init__(self, source):
        self.source = str(source)
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {self.source}")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def frames(self):
        """Yield (frame_index, frame) until the stream ends."""
        idx = 0
        while True:
            ok, frame = self.cap.read()
            if not ok:
                break
            yield idx, frame
            idx += 1

    def release(self):
        if self.cap:
            self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.release()
