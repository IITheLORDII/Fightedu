"""Küçük 3B vektör/çerçeve yardımcıları ve keyframe enterpolasyonu (saf Python).

Dünya koordinatları (cm):  X = ileri (rakibe/hedefe doğru), Y = yukarı, Z = sporcunun sağı.
Bir "çerçeve" (frame) üç birim vektördür: (f, u, r) = (ileri, yukarı, sağ).
"""
import math


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def length(a):
    return math.sqrt(dot(a, a))


def unit(a, fallback=(1.0, 0.0, 0.0)):
    n = length(a)
    return mul(a, 1.0 / n) if n > 1e-9 else fallback


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def madd(*terms):
    """madd(p, (v, s), (w, t), ...) = p + v*s + w*t ..."""
    x, y, z = terms[0]
    for v, s in terms[1:]:
        x += v[0] * s
        y += v[1] * s
        z += v[2] * s
    return (x, y, z)


def reject(v, axis):
    """v'nin axis'e dik bileşeni."""
    return sub(v, mul(axis, dot(v, axis)))


WORLD = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def rotate_frame(frame, yaw=0.0, pitch=0.0, roll=0.0):
    """Çerçeveyi kendi eksenlerine göre döndür.

    yaw   (+): sağa dön (ileri vektör sağa doğru)      – yukarı ekseni etrafında
    pitch (+): öne eğil (yukarı vektör ileri doğru)     – sağ ekseni etrafında
    roll  (+): sağa yatış (yukarı vektör sağa doğru)    – ileri ekseni etrafında
    """
    f, u, r = frame
    if yaw:
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        f, r = madd((0, 0, 0), (f, c), (r, s)), madd((0, 0, 0), (r, c), (f, -s))
    if pitch:
        c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        f, u = madd((0, 0, 0), (f, c), (u, -s)), madd((0, 0, 0), (u, c), (f, s))
    if roll:
        c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        u, r = madd((0, 0, 0), (u, c), (r, s)), madd((0, 0, 0), (r, c), (u, -s))
    return (f, u, r)


def in_frame(frame, origin, x=0.0, y=0.0, z=0.0):
    """Çerçeve yerel koordinatından (ileri, yukarı, sağ) dünya noktasına."""
    f, u, r = frame
    return madd(origin, (f, x), (u, y), (r, z))


def dir_in_frame(frame, x=0.0, y=0.0, z=0.0):
    f, u, r = frame
    return madd((0, 0, 0), (f, x), (u, y), (r, z))


def to_frame(frame, v):
    """Dünya vektörünü çerçeve koordinatına (ileri, yukarı, sağ)."""
    f, u, r = frame
    return (dot(v, f), dot(v, u), dot(v, r))


def yaw_frame(yaw):
    return rotate_frame(WORLD, yaw=yaw)


# --------------------------------------------------------------------------
# Enterpolasyon: periyodik, aşmayan (monotone) kübik Hermite (Fritsch–Carlson)
# --------------------------------------------------------------------------
def _pchip_slopes(ts, ys):
    n = len(ts)
    h = [ts[i + 1] - ts[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] if h[i] else 0.0 for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    return m, d, h


def periodic_pchip(times, values, period):
    """times: artan keyframe zamanları (0 dahil, period hariç); values: aynı uzunlukta liste.
    Döngüsel (son -> ilk) yumuşak, aşmasız enterpolasyon fonksiyonu döner."""
    n = len(times)
    if n == 1:
        v = values[0]
        return lambda t: v
    # iki uçtan birer tur genişlet (periyodik eğimler için)
    ts = [times[-2] - period, times[-1] - period] + list(times) + [times[0] + period, times[1] + period]
    ys = [values[-2], values[-1]] + list(values) + [values[0], values[1]]
    m, _d, _h = _pchip_slopes(ts, ys)

    def f(t):
        t = t % period
        # aralığı bul
        k = 2
        while k < len(ts) - 1 and ts[k + 1] <= t:
            k += 1
        t0, t1 = ts[k], ts[k + 1]
        hh = t1 - t0
        s = (t - t0) / hh if hh else 0.0
        y0, y1 = ys[k], ys[k + 1]
        m0, m1 = m[k] * hh, m[k + 1] * hh
        s2, s3 = s * s, s * s * s
        return ((2 * s3 - 3 * s2 + 1) * y0 + (s3 - 2 * s2 + s) * m0
                + (-2 * s3 + 3 * s2) * y1 + (s3 - s2) * m1)

    return f


def smoothstep(e0, e1, x):
    if e1 == e0:
        return 1.0 if x >= e1 else 0.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)
