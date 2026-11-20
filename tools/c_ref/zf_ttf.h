/* zf_ttf.h — the C twin of src/text/ttf.axle, outline.axle and gfx/coverage.axle.
 *
 * TrueType (glyf) fonts only: head, maxp, hhea, hmtx, cmap (formats 4 and 12), loca, glyf with
 * composites. No hinting, no CFF, no variable fonts. Kerning comes from GPOS `kern` (zf_gpos).
 */
#ifndef ZF_TTF_H
#define ZF_TTF_H
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    const uint8_t *d;
    int len;
    int unitsPerEm, locaFormat, numGlyphs, numHMetrics, ascent, descent, lineGap;
    int loca, glyf, hmtx, cmap, gpos;
    int cmapFormat, cmapOff; /* chosen subtable: absolute offset */
} Ttf;

static inline int zf_u16(const Ttf *t, int off) {
    if (off < 0 || off + 2 > t->len) return 0;
    return (t->d[off] << 8) | t->d[off + 1];
}
static inline int zf_i16(const Ttf *t, int off) {
    int v = zf_u16(t, off);
    return v >= 32768 ? v - 65536 : v;
}
static inline int64_t zf_u32(const Ttf *t, int off) {
    return ((int64_t)zf_u16(t, off) << 16) | zf_u16(t, off + 2);
}

static int ttf_table(const Ttf *t, const char *tag) {
    int n = zf_u16(t, 4);
    for (int i = 0; i < n; i++) {
        int rec = 12 + i * 16;
        if (rec + 16 > t->len) return 0;
        if (memcmp(t->d + rec, tag, 4) == 0) return (int)zf_u32(t, rec + 8);
    }
    return 0;
}

/* 1 on success. */
static int ttf_open(Ttf *t, const uint8_t *d, int len) {
    memset(t, 0, sizeof *t);
    t->d = d; t->len = len;
    if (len < 12) return 0;
    int64_t tag = zf_u32(t, 0);
    if (tag != 0x00010000 && tag != 0x74727565) return 0;
    int head = ttf_table(t, "head"), maxp = ttf_table(t, "maxp"), hhea = ttf_table(t, "hhea");
    t->hmtx = ttf_table(t, "hmtx"); t->loca = ttf_table(t, "loca"); t->glyf = ttf_table(t, "glyf");
    t->cmap = ttf_table(t, "cmap"); t->gpos = ttf_table(t, "GPOS");
    if (!head || !maxp || !hhea || !t->hmtx || !t->loca || !t->glyf || !t->cmap) return 0;
    t->unitsPerEm = zf_u16(t, head + 18);
    t->locaFormat = zf_i16(t, head + 50);
    t->numGlyphs = zf_u16(t, maxp + 4);
    t->ascent = zf_i16(t, hhea + 4); t->descent = zf_i16(t, hhea + 6); t->lineGap = zf_i16(t, hhea + 8);
    t->numHMetrics = zf_u16(t, hhea + 34);
    if (t->unitsPerEm <= 0 || t->numGlyphs <= 0 || t->numHMetrics <= 0) return 0;
    /* choose the cmap subtable: (3,10) fmt 12, else (3,1) fmt 4, else (0,*) */
    int n = zf_u16(t, t->cmap + 2), best = -1, bestScore = -1;
    for (int i = 0; i < n; i++) {
        int rec = t->cmap + 4 + i * 8;
        int plat = zf_u16(t, rec), enc = zf_u16(t, rec + 2);
        int off = t->cmap + (int)zf_u32(t, rec + 4);
        int fmt = zf_u16(t, off);
        int score = -1;
        if (plat == 3 && enc == 10 && fmt == 12) score = 4;
        else if (plat == 0 && fmt == 12) score = 3;
        else if (plat == 3 && enc == 1 && fmt == 4) score = 2;
        else if (plat == 0 && fmt == 4) score = 1;
        if (score > bestScore) { bestScore = score; best = off; }
    }
    if (best < 0) return 0;
    t->cmapOff = best; t->cmapFormat = zf_u16(t, best);
    return 1;
}

static int ttf_glyph_index(const Ttf *t, int cp) {
    int o = t->cmapOff;
    if (t->cmapFormat == 4) {
        if (cp > 0xFFFF) return 0;
        int segX2 = zf_u16(t, o + 6), seg = segX2 / 2;
        int endC = o + 14, startC = endC + segX2 + 2, delta = startC + segX2, range = delta + segX2;
        for (int i = 0; i < seg; i++) {
            if (cp <= zf_u16(t, endC + i * 2)) {
                int s = zf_u16(t, startC + i * 2);
                if (cp < s) return 0;
                int ro = zf_u16(t, range + i * 2);
                if (ro == 0) return (cp + zf_u16(t, delta + i * 2)) & 0xFFFF;
                int g = zf_u16(t, range + i * 2 + ro + (cp - s) * 2);
                return g == 0 ? 0 : (g + zf_u16(t, delta + i * 2)) & 0xFFFF;
            }
        }
        return 0;
    }
    int64_t groups = zf_u32(t, o + 12);
    for (int64_t i = 0; i < groups; i++) {
        int g = o + 16 + (int)i * 12;
        int64_t s = zf_u32(t, g), e = zf_u32(t, g + 4);
        if (cp < s) return 0;
        if (cp <= e) return (int)(zf_u32(t, g + 8) + (cp - s));
    }
    return 0;
}

static int ttf_advance(const Ttf *t, int g) {
    int i = g < t->numHMetrics ? g : t->numHMetrics - 1;
    return zf_u16(t, t->hmtx + i * 4);
}

/* ---- outlines ------------------------------------------------------------------------- */

#define ZF_MAX_POINTS 4096
#define ZF_MAX_CONTOURS 256
typedef struct {
    int n, nc;
    double x[ZF_MAX_POINTS], y[ZF_MAX_POINTS];
    uint8_t on[ZF_MAX_POINTS];
    int end[ZF_MAX_CONTOURS];
} Outline;

static int ttf_glyph_range(const Ttf *t, int g, int *off, int *len) {
    if (g < 0 || g >= t->numGlyphs) return 0;
    int a, b;
    if (t->locaFormat == 0) { a = zf_u16(t, t->loca + g * 2) * 2; b = zf_u16(t, t->loca + g * 2 + 2) * 2; }
    else { a = (int)zf_u32(t, t->loca + g * 4); b = (int)zf_u32(t, t->loca + g * 4 + 4); }
    *off = t->glyf + a; *len = b - a;
    return b > a;
}

/* Append glyph g, transformed by (a b c d tx ty), to o. Returns 0 on overflow or corruption. */
static int ttf_outline(const Ttf *t, int g, Outline *o, double a, double b, double c, double d,
                       double tx, double ty, int depth) {
    int off, len;
    if (!ttf_glyph_range(t, g, &off, &len)) return 1; /* an empty glyph is not an error */
    if (depth > 6) return 0;
    int nc = zf_i16(t, off);
    int p = off + 10;
    if (nc >= 0) {
        if (o->nc + nc > ZF_MAX_CONTOURS) return 0;
        int base = o->n, last = -1;
        for (int i = 0; i < nc; i++) { last = zf_u16(t, p + i * 2); o->end[o->nc + i] = base + last; }
        p += nc * 2;
        int np = last + 1;
        if (base + np > ZF_MAX_POINTS) return 0;
        int ilen = zf_u16(t, p); p += 2 + ilen;
        uint8_t flags[ZF_MAX_POINTS];
        for (int i = 0; i < np;) {
            int f = t->d[p++];
            flags[i++] = (uint8_t)f;
            if (f & 8) { int r = t->d[p++]; while (r-- > 0 && i < np) flags[i++] = (uint8_t)f; }
        }
        int xs[ZF_MAX_POINTS], ys[ZF_MAX_POINTS], v = 0;
        for (int i = 0; i < np; i++) {
            int f = flags[i];
            if (f & 2) { int dx = t->d[p++]; v += (f & 16) ? dx : -dx; }
            else if (!(f & 16)) { v += zf_i16(t, p); p += 2; }
            xs[i] = v;
        }
        v = 0;
        for (int i = 0; i < np; i++) {
            int f = flags[i];
            if (f & 4) { int dy = t->d[p++]; v += (f & 32) ? dy : -dy; }
            else if (!(f & 32)) { v += zf_i16(t, p); p += 2; }
            ys[i] = v;
        }
        for (int i = 0; i < np; i++) {
            o->x[base + i] = a * xs[i] + c * ys[i] + tx;
            o->y[base + i] = b * xs[i] + d * ys[i] + ty;
            o->on[base + i] = flags[i] & 1;
        }
        o->n += np; o->nc += nc;
        return 1;
    }
    for (;;) {
        int fl = zf_u16(t, p), gi = zf_u16(t, p + 2);
        p += 4;
        double dx, dy;
        if (fl & 1) { dx = zf_i16(t, p); dy = zf_i16(t, p + 2); p += 4; }
        else { dx = (int8_t)t->d[p]; dy = (int8_t)t->d[p + 1]; p += 2; }
        if (!(fl & 2)) { dx = 0; dy = 0; } /* point matching is not supported: place at the origin */
        double ma = 1, mb = 0, mc = 0, md = 1;
        if (fl & 8) { ma = md = zf_i16(t, p) / 16384.0; p += 2; }
        else if (fl & 0x40) { ma = zf_i16(t, p) / 16384.0; md = zf_i16(t, p + 2) / 16384.0; p += 4; }
        else if (fl & 0x80) {
            ma = zf_i16(t, p) / 16384.0; mb = zf_i16(t, p + 2) / 16384.0;
            mc = zf_i16(t, p + 4) / 16384.0; md = zf_i16(t, p + 6) / 16384.0; p += 8;
        }
        /* child transform T = M, then parent: x' = a*(ma x + mc y + dx) + c*(mb x + md y + dy) + tx ... */
        double na = a * ma + c * mb, nb = b * ma + d * mb, nc2 = a * mc + c * md, nd = b * mc + d * md;
        double ntx = a * dx + c * dy + tx, nty = b * dx + d * dy + ty;
        if (!ttf_outline(t, gi, o, na, nb, nc2, nd, ntx, nty, depth + 1)) return 0;
        if (!(fl & 0x20)) break;
    }
    return 1;
}

/* ---- coverage ------------------------------------------------------------------------- */

typedef struct { int w, h; double *a; } Cover;

static void cover_init(Cover *c, int w, int h) {
    c->w = w; c->h = h;
    c->a = (double *)calloc((size_t)w * h + 4, sizeof(double));
}

static inline void cover_add(Cover *c, int idx, double v) {
    if (idx >= 0 && idx < c->w * c->h) c->a[idx] += v;
}

/* Signed-area accumulation of one edge (after Raph Levien's font-rs). */
static void cover_line(Cover *c, double x0, double y0, double x1, double y1) {
    if (y0 == y1) return;
    double dir = 1.0;
    if (y0 > y1) { double tx = x0, ty = y0; x0 = x1; y0 = y1; x1 = tx; y1 = ty; dir = -1.0; }
    double dxdy = (x1 - x0) / (y1 - y0);
    double x = x0;
    if (y0 < 0) { x -= y0 * dxdy; y0 = 0; }
    int ys = (int)floor(y0);
    int ye = (int)ceil(y1); if (ye > c->h) ye = c->h;
    for (int y = ys; y < ye; y++) {
        int ls = y * c->w;
        double top = y > y0 ? (double)y : y0;
        double bot = (y + 1) < y1 ? (double)(y + 1) : y1;
        double dy = bot - top;
        double xn = x + dxdy * dy;
        double dd = dy * dir;
        double xa = x < xn ? x : xn, xb = x < xn ? xn : x;
        double xaf = floor(xa);
        int xai = (int)xaf;
        double xbc = ceil(xb);
        int xbi = (int)xbc;
        if (xbi <= xai + 1) {
            double xmf = 0.5 * (x + xn) - xaf;
            cover_add(c, ls + xai, dd - dd * xmf);
            cover_add(c, ls + xai + 1, dd * xmf);
        } else {
            double s = 1.0 / (xb - xa);
            double x0f = xa - xaf;
            double a0 = 0.5 * s * (1.0 - x0f) * (1.0 - x0f);
            double x1f = xb - xbc + 1.0;
            double am = 0.5 * s * x1f * x1f;
            cover_add(c, ls + xai, dd * a0);
            if (xbi == xai + 2) {
                cover_add(c, ls + xai + 1, dd * (1.0 - a0 - am));
            } else {
                double a1 = s * (1.5 - x0f);
                cover_add(c, ls + xai + 1, dd * (a1 - a0));
                for (int xi = xai + 2; xi < xbi - 1; xi++) cover_add(c, ls + xi, dd * s);
                double a2 = a1 + (double)(xbi - xai - 3) * s;
                cover_add(c, ls + xbi - 1, dd * (1.0 - a2 - am));
            }
            cover_add(c, ls + xbi, dd * am);
        }
        x = xn;
    }
}

static void cover_quad(Cover *c, double x0, double y0, double x1, double y1, double x2, double y2) {
    double ddx = x0 - 2 * x1 + x2, ddy = y0 - 2 * y1 + y2;
    double dd = sqrt(ddx * ddx + ddy * ddy);
    int n = (int)ceil(sqrt(dd * 12.5));
    if (n < 1) n = 1;
    if (n > 32) n = 32;
    double px = x0, py = y0;
    for (int i = 1; i <= n; i++) {
        double t = (double)i / n, u = 1.0 - t;
        double qx = u * u * x0 + 2 * u * t * x1 + t * t * x2;
        double qy = u * u * y0 + 2 * u * t * y1 + t * t * y2;
        cover_line(c, px, py, qx, qy);
        px = qx; py = qy;
    }
}

/* Prefix-sum each row into 0..255 coverage. */
static void cover_finish(const Cover *c, uint8_t *out) {
    for (int y = 0; y < c->h; y++) {
        double acc = 0.0;
        for (int x = 0; x < c->w; x++) {
            acc += c->a[y * c->w + x];
            double v = fabs(acc); if (v > 1.0) v = 1.0;
            out[y * c->w + x] = (uint8_t)floor(v * 255.0 + 0.5);
        }
    }
}

/* ---- one glyph to a bitmap ------------------------------------------------------------ */

typedef struct { int w, h, left, top; uint8_t *px; } GlyphBitmap; /* top: rows above the baseline */

/* Walk one contour (points start .. start+n-1 of o) into the coverage buffer. Off-curve points
 * between two off-curve points imply an on-curve midpoint; the contour may start off-curve. */
static void ttf_contour(Cover *c, const Outline *o, int start, int n, double s, double sub, int left, int top) {
    double X[ZF_MAX_POINTS], Y[ZF_MAX_POINTS];
    uint8_t N[ZF_MAX_POINTS];
    for (int i = 0; i < n; i++) {
        X[i] = o->x[start + i] * s + sub - left;
        Y[i] = -o->y[start + i] * s - top;
        N[i] = o->on[start + i];
    }
    double sx, sy;
    int from, to; /* walk X[from .. to) in order */
    if (N[0]) { sx = X[0]; sy = Y[0]; from = 1; to = n; }
    else if (N[n - 1]) { sx = X[n - 1]; sy = Y[n - 1]; from = 0; to = n - 1; }
    else { sx = (X[n - 1] + X[0]) * 0.5; sy = (Y[n - 1] + Y[0]) * 0.5; from = 0; to = n; }
    double cx = sx, cy = sy, ox = 0, oy = 0;
    int pending = 0;
    for (int i = from; i < to; i++) {
        if (N[i]) {
            if (pending) cover_quad(c, cx, cy, ox, oy, X[i], Y[i]);
            else cover_line(c, cx, cy, X[i], Y[i]);
            cx = X[i]; cy = Y[i]; pending = 0;
        } else {
            if (pending) {
                double mx = (ox + X[i]) * 0.5, my = (oy + Y[i]) * 0.5;
                cover_quad(c, cx, cy, ox, oy, mx, my);
                cx = mx; cy = my;
            }
            ox = X[i]; oy = Y[i]; pending = 1;
        }
    }
    if (pending) cover_quad(c, cx, cy, ox, oy, sx, sy);
    else cover_line(c, cx, cy, sx, sy);
}

/* Rasterise glyph g at `px` pixels per em, shifted right by `sub` (0..1) of a pixel. */
static int ttf_raster(const Ttf *t, int g, double px, double sub, GlyphBitmap *out) {
    static Outline o;
    memset(out, 0, sizeof *out);
    o.n = 0; o.nc = 0;
    if (!ttf_outline(t, g, &o, 1, 0, 0, 1, 0, 0, 0)) return 0;
    if (o.n == 0) return 1;
    double s = px / t->unitsPerEm;
    double minx = 1e30, maxx = -1e30, miny = 1e30, maxy = -1e30;
    for (int i = 0; i < o.n; i++) {
        double X = o.x[i] * s + sub, Y = -o.y[i] * s; /* y down */
        if (X < minx) minx = X;
        if (X > maxx) maxx = X;
        if (Y < miny) miny = Y;
        if (Y > maxy) maxy = Y;
    }
    int left = (int)floor(minx) - 1, top = (int)floor(miny) - 1;
    int right = (int)ceil(maxx) + 1, bottom = (int)ceil(maxy) + 1;
    int w = right - left, h = bottom - top;
    Cover c; cover_init(&c, w + 2, h);
    int start = 0;
    for (int ci = 0; ci < o.nc; ci++) {
        int end = o.end[ci], n = end - start + 1;
        if (n >= 2) ttf_contour(&c, &o, start, n, s, sub, left, top);
        start = end + 1;
    }
    out->w = w + 2; out->h = h; out->left = left; out->top = -top;
    out->px = (uint8_t *)calloc((size_t)out->w * out->h, 1);
    cover_finish(&c, out->px);
    free(c.a);
    return 1;
}

#endif
