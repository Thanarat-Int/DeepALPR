"""IoU-based plate tracker with speed estimation (SORT-lite, no Kalman).

Each plate gets a stable track id across frames so it is counted once and so
multiple OCR readings can be combined (multi-frame voting). Speed is estimated
from how far the plate's centroid travels over the track's lifetime.
"""
from collections import Counter


def iou(a, b) -> float:
    """Intersection-over-union of two (x1, y1, x2, y2) boxes."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _centroid(box):
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


class Track:
    def __init__(self, track_id, bbox, frame_idx):
        self.id = track_id
        self.bbox = bbox
        cx, cy = _centroid(bbox)
        self.history = [(frame_idx, cx, cy)]   # (frame, cx, cy)
        self.hits = 1
        self.missed = 0
        # multi-frame OCR voting
        self.votes: Counter[str] = Counter()        # text -> summed confidence
        self.vote_counts: Counter[str] = Counter()  # text -> number of readings
        self._crops: dict = {}                      # text -> (best_conf, crop)
        self.reading_count = 0
        self.speed_kmh = 0.0
        self.emitted = False
        # Vehicle colour voting (one vote per frame the track is alive)
        self.color_votes: Counter[str] = Counter()       # "white" -> count
        self.color_th_for: dict[str, str] = {}           # "white" -> "ขาว"
        self._color_conf_sum: dict[str, float] = {}      # for averaging

    def update(self, bbox, frame_idx):
        self.bbox = bbox
        cx, cy = _centroid(bbox)
        self.history.append((frame_idx, cx, cy))
        self.hits += 1
        self.missed = 0

    def predicted_bbox(self):
        """Extrapolate the next box from recent motion -- lets the tracker
        follow a fast-moving plate that would otherwise lose IoU overlap."""
        if len(self.history) < 2:
            return self.bbox
        ref = self.history[-min(5, len(self.history))]
        last = self.history[-1]
        df = max(last[0] - ref[0], 1)
        steps = self.missed + 1
        dx = (last[1] - ref[1]) / df * steps
        dy = (last[2] - ref[2]) / df * steps
        x1, y1, x2, y2 = self.bbox
        return (x1 + dx, y1 + dy, x2 + dx, y2 + dy)

    def add_reading(self, text, conf, crop):
        """Record one OCR attempt for this plate."""
        if not text:
            return
        self.votes[text] += conf
        self.vote_counts[text] += 1
        self.reading_count += 1
        # Keep the sharpest crop *per text* so the saved image always matches
        # the voted plate -- even if the tracker briefly merged two vehicles.
        prev = self._crops.get(text)
        if crop is not None and (prev is None or conf > prev[0]):
            self._crops[text] = (conf, crop)

    def best_plate(self) -> tuple[str, float]:
        """Voted plate string and its confidence.

        The winner is the string with the most summed confidence; its
        confidence is the *mean* over the readings that agreed on it -- so
        garbage readings from far-away frames (which vote for other strings)
        do not dilute a correct, consistently-read plate.
        """
        if not self.votes:
            return "", 0.0
        text, weight = self.votes.most_common(1)[0]
        return text, min(weight / max(self.vote_counts[text], 1), 1.0)

    def best_crop(self):
        """Highest-confidence crop among readings that produced the voted plate."""
        if not self.votes:
            return None
        text, _ = self.votes.most_common(1)[0]
        entry = self._crops.get(text)
        return entry[1] if entry else None

    def add_color(self, label_en: str, label_th: str, conf: float):
        """Record one colour vote for this vehicle."""
        if not label_en or label_en == "unknown":
            return
        self.color_votes[label_en] += 1
        self.color_th_for[label_en] = label_th
        self._color_conf_sum[label_en] = (
            self._color_conf_sum.get(label_en, 0.0) + conf)

    def best_color(self) -> tuple[str, str, float]:
        """Most-voted vehicle colour across the track lifetime."""
        if not self.color_votes:
            return "unknown", "", 0.0
        label, n = self.color_votes.most_common(1)[0]
        avg_conf = self._color_conf_sum[label] / max(n, 1)
        return label, self.color_th_for.get(label, ""), avg_conf

    def estimate_speed(self, fps, meters_per_pixel) -> float:
        """Average speed over the track lifetime, in km/h."""
        if len(self.history) < 2:
            return 0.0
        f0, x0, y0 = self.history[0]
        f1, x1, y1 = self.history[-1]
        frames = f1 - f0
        if frames <= 0:
            return 0.0
        dist_px = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        seconds = frames / fps
        speed_ms = (dist_px * meters_per_pixel) / seconds
        self.speed_kmh = speed_ms * 3.6
        return self.speed_kmh


class PlateTracker:
    def __init__(self, iou_threshold=0.3, max_age=30):
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.tracks: list[Track] = []
        self._next_id = 1

    def update(self, detections, frame_idx) -> tuple[list[Track], list[Track]]:
        """Match detections to tracks. Returns (active_tracks, retired_tracks)."""
        unmatched = set(range(len(detections)))

        for track in self.tracks:
            predicted = track.predicted_bbox()
            best_j, best_score = -1, self.iou_threshold
            for j in unmatched:
                score = iou(predicted, detections[j])
                if score >= best_score:
                    best_score, best_j = score, j
            if best_j >= 0:
                track.update(detections[best_j], frame_idx)
                unmatched.discard(best_j)
            else:
                track.missed += 1

        for j in unmatched:
            self.tracks.append(Track(self._next_id, detections[j], frame_idx))
            self._next_id += 1

        retired = [t for t in self.tracks if t.missed > self.max_age]
        self.tracks = [t for t in self.tracks if t.missed <= self.max_age]
        return self.tracks, retired
