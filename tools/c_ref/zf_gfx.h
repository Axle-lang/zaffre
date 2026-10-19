/* zf_gfx.h — the C twin of src/gfx/*.axle.
 *
 * The Axle was written where no compiler was available, so the numeric kernels are written
 * here first, in a language that runs, looked at (tools/c_ref/test_gfx.c writes PNG-able PPMs),
 * and then transliterated line for line. Names, argument order and the order of operations
 * match the Axle files; an edit to one is an edit to the other.
 *
 * Conventions shared with the Axle:
 *   - pixels are 0x00RRGGBB in a plane of uint32_t (smalt's Frame);
 *   - the centre of pixel (x, y) is (x + 0.5, y + 0.5);
 *   - coverage and alpha are 0..255 integers at the edges of every function, doubles inside.
 */
#ifndef ZF_GFX_H
#define ZF_GFX_H
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint32_t *px; int w, h; int cx0, cy0, cx1, cy1; int opacity; } Canvas;

typedef struct { double x, y, w, h, tl, tr, br, bl; } RRect;

/* A fill: solid, or a linear gradient from (gx0,gy0) to (gx1,gy1). Alphas are 0..255. */
typedef struct { int kind; int rgb0, rgb1, a0, a1; double gx0, gy0, gx1, gy1; } Brush;

static inline int zf_min(int a, int b) { return a < b ? a : b; }
static inline int zf_max(int a, int b) { return a > b ? a : b; }
static inline double zf_clamp01(double v) { return v < 0.0 ? 0.0 : (v > 1.0 ? 1.0 : v); }

static inline int zf_div255(int t) { return (t + 128 + ((t + 128) >> 8)) >> 8; }

/* dst with `rgb` over it at alpha a (0..255). */
static inline uint32_t zf_over(uint32_t dst, uint32_t rgb, int a) {
    if (a <= 0) return dst;
    if (a >= 255) return rgb;
    int ia = 255 - a;
    int r = zf_div255((int)((dst >> 16) & 255) * ia + (int)((rgb >> 16) & 255) * a);
    int g = zf_div255((int)((dst >> 8) & 255) * ia + (int)((rgb >> 8) & 255) * a);
    int b = zf_div255((int)(dst & 255) * ia + (int)(rgb & 255) * a);
    return (uint32_t)((r << 16) | (g << 8) | b);
}

static inline void zf_put(Canvas *c, int x, int y, uint32_t rgb, int a) {
    if (x < c->cx0 || x >= c->cx1 || y < c->cy0 || y >= c->cy1) return;
    int e = c->opacity >= 255 ? a : zf_div255(a * c->opacity);
    uint32_t *p = &c->px[(size_t)y * c->w + x];
    *p = zf_over(*p, rgb, e);
}

/* ---- shapes -------------------------------------------------------------------------- */

static inline RRect zf_rrect(double x, double y, double w, double h, double tl, double tr, double br, double bl) {
    double m = (w < h ? w : h) * 0.5;
    RRect r = { x, y, w, h,
        tl > m ? m : (tl < 0 ? 0 : tl), tr > m ? m : (tr < 0 ? 0 : tr),
        br > m ? m : (br < 0 ? 0 : br), bl > m ? m : (bl < 0 ? 0 : bl) };
    return r;
}
static inline RRect zf_rrect_u(double x, double y, double w, double h, double r) {
    return zf_rrect(x, y, w, h, r, r, r, r);
}

/* Signed distance from (px, py) to the outline: negative inside. */
static inline double zf_sdf(const RRect *rr, double px, double py) {
    double hx = rr->w * 0.5, hy = rr->h * 0.5;
    double dx = px - (rr->x + hx), dy = py - (rr->y + hy);
    double r = dx < 0 ? (dy < 0 ? rr->tl : rr->bl) : (dy < 0 ? rr->tr : rr->br);
    double qx = fabs(dx) - (hx - r), qy = fabs(dy) - (hy - r);
    double ox = qx > 0 ? qx : 0, oy = qy > 0 ? qy : 0;
    double outside = (ox > 0 && oy > 0) ? sqrt(ox * ox + oy * oy) : (ox > oy ? ox : oy);
    double inside = qx > qy ? qx : qy;
    if (inside > 0) inside = 0;
    return outside + inside - r;
}

/* Coverage of the pixel whose centre is at signed distance d: a one-pixel linear ramp. */
static inline double zf_cover(double d) { return zf_clamp01(0.5 - d); }

static const int ZF_BAYER4[16] = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 };

static inline Brush zf_solid(int rgb, int a) { Brush b = { 0, rgb, rgb, a, a, 0, 0, 0, 0 }; return b; }
static inline Brush zf_linear(int rgb0, int a0, int rgb1, int a1, double x0, double y0, double x1, double y1) {
    Brush b = { 1, rgb0, rgb1, a0, a1, x0, y0, x1, y1 }; return b;
}

/* The brush at pixel (x, y): colour in *rgb, alpha (0..255) returned. */
static inline int zf_brush_at(const Brush *b, int x, int y, uint32_t *rgb) {
    if (b->kind == 0) { *rgb = (uint32_t)b->rgb0; return b->a0; }
    double ax = b->gx1 - b->gx0, ay = b->gy1 - b->gy0;
    double len2 = ax * ax + ay * ay;
    double t = len2 > 0.0 ? ((x + 0.5 - b->gx0) * ax + (y + 0.5 - b->gy0) * ay) / len2 : 0.0;
    t = zf_clamp01(t);
    double dith = ((double)ZF_BAYER4[(y & 3) * 4 + (x & 3)] - 7.5) / 16.0;
    int r0 = (b->rgb0 >> 16) & 255, g0 = (b->rgb0 >> 8) & 255, b0 = b->rgb0 & 255;
    int r1 = (b->rgb1 >> 16) & 255, g1 = (b->rgb1 >> 8) & 255, b1 = b->rgb1 & 255;
    int r = (int)floor(r0 + (r1 - r0) * t + 0.5 + dith); if (r < 0) r = 0; if (r > 255) r = 255;
    int g = (int)floor(g0 + (g1 - g0) * t + 0.5 + dith); if (g < 0) g = 0; if (g > 255) g = 255;
    int bl = (int)floor(b0 + (b1 - b0) * t + 0.5 + dith); if (bl < 0) bl = 0; if (bl > 255) bl = 255;
    *rgb = (uint32_t)((r << 16) | (g << 8) | bl);
    return (int)floor(b->a0 + (b->a1 - b->a0) * t + 0.5);
}

/* One pixel of a shape: coverage cv (0..1) of brush `b`. */
static inline void zf_shape_px(Canvas *c, const Brush *b, int x, int y, double cv) {
    if (cv <= 0.0) return;
    uint32_t rgb;
    int a = zf_brush_at(b, x, y, &rgb);
    int e = (int)floor(a * cv + 0.5);
    if (e > 0) zf_put(c, x, y, rgb, e);
}

/* Fill (bw = 0) or stroke-inside (bw > 0) the rounded rectangle. */
static void zf_shape(Canvas *c, const RRect *rr, double bw, const Brush *b) {
    int ix0 = (int)floor(rr->x), ix1 = (int)ceil(rr->x + rr->w);
    int iy0 = (int)floor(rr->y), iy1 = (int)ceil(rr->y + rr->h);
    int rl = (int)ceil((rr->tl > rr->bl ? rr->tl : rr->bl) + bw) + 1;
    int rrr = (int)ceil((rr->tr > rr->br ? rr->tr : rr->br) + bw) + 1;
    int y0 = zf_max(iy0, c->cy0), y1 = zf_min(iy1, c->cy1);
    for (int y = y0; y < y1; y++) {
        double py = y + 0.5;
        int leftEnd = zf_min(ix1, ix0 + rl);
        int rightStart = zf_max(leftEnd, ix1 - rrr);
        for (int zone = 0; zone < 2; zone++) {
            int xa = zone == 0 ? ix0 : rightStart;
            int xb = zone == 0 ? leftEnd : ix1;
            xa = zf_max(xa, c->cx0); xb = zf_min(xb, c->cx1);
            for (int x = xa; x < xb; x++) {
                double d = zf_sdf(rr, x + 0.5, py);
                double cv = zf_cover(d);
                if (bw > 0) cv -= zf_cover(d + bw);
                zf_shape_px(c, b, x, y, cv);
            }
        }
        if (rightStart > leftEnd) {
            double d = zf_sdf(rr, leftEnd + 0.5, py);
            double cv = zf_cover(d);
            if (bw > 0) cv -= zf_cover(d + bw);
            if (cv > 0.0) {
                int xa = zf_max(leftEnd, c->cx0), xb = zf_min(rightStart, c->cx1);
                for (int x = xa; x < xb; x++) zf_shape_px(c, b, x, y, cv);
            }
        }
    }
}

/* A soft shadow: the outline offset by (dx, dy) and grown by `spread`, faded over `blur`. */
static void zf_shadow(Canvas *c, const RRect *rr, double dx, double dy, double blur, double spread,
                      int rgb, int alpha) {
    RRect s = zf_rrect(rr->x + dx - spread, rr->y + dy - spread, rr->w + 2 * spread, rr->h + 2 * spread,
                       rr->tl + spread, rr->tr + spread, rr->br + spread, rr->bl + spread);
    if (blur < 0.5) blur = 0.5;
    int x0 = zf_max((int)floor(s.x - blur), c->cx0), x1 = zf_min((int)ceil(s.x + s.w + blur), c->cx1);
    int y0 = zf_max((int)floor(s.y - blur), c->cy0), y1 = zf_min((int)ceil(s.y + s.h + blur), c->cy1);
    for (int y = y0; y < y1; y++) {
        for (int x = x0; x < x1; x++) {
            double d = zf_sdf(&s, x + 0.5, y + 0.5);
            double t = zf_clamp01((blur - d) / (2.0 * blur));
            double cv = t * t * (3.0 - 2.0 * t);
            int e = (int)floor(alpha * cv + 0.5);
            if (e > 0) zf_put(c, x, y, (uint32_t)rgb, e);
        }
    }
}

/* A line segment with round caps. */
static void zf_capsule(Canvas *c, double x0, double y0, double x1, double y1, double width, int rgb, int alpha) {
    double hw = width * 0.5;
    int bx0 = zf_max((int)floor((x0 < x1 ? x0 : x1) - hw - 1), c->cx0);
    int bx1 = zf_min((int)ceil((x0 < x1 ? x1 : x0) + hw + 1), c->cx1);
    int by0 = zf_max((int)floor((y0 < y1 ? y0 : y1) - hw - 1), c->cy0);
    int by1 = zf_min((int)ceil((y0 < y1 ? y1 : y0) + hw + 1), c->cy1);
    double vx = x1 - x0, vy = y1 - y0, len2 = vx * vx + vy * vy;
    for (int y = by0; y < by1; y++) {
        for (int x = bx0; x < bx1; x++) {
            double px = x + 0.5 - x0, py = y + 0.5 - y0;
            double t = len2 > 0 ? zf_clamp01((px * vx + py * vy) / len2) : 0.0;
            double ex = px - vx * t, ey = py - vy * t;
            double d = sqrt(ex * ex + ey * ey) - hw;
            int e = (int)floor(alpha * zf_cover(d) + 0.5);
            if (e > 0) zf_put(c, x, y, (uint32_t)rgb, e);
        }
    }
}

/* A coverage mask (one byte per pixel) tinted and blended at (x, y). */
static void zf_mask(Canvas *c, int x, int y, const uint8_t *m, int mw, int mh, int stride, int rgb, int alpha) {
    for (int j = 0; j < mh; j++) {
        int py = y + j;
        if (py < c->cy0 || py >= c->cy1) continue;
        for (int i = 0; i < mw; i++) {
            int cv = m[j * stride + i];
            if (cv == 0) continue;
            zf_put(c, x + i, py, (uint32_t)rgb, zf_div255(cv * alpha));
        }
    }
}

#endif
