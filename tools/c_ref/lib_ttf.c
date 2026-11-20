/* lib_ttf.c — a thin C ABI over zf_ttf.h so Python's ctypes can drive it against FreeType. */
#include "zf_ttf.h"
static Ttf T;
int zt_open(const uint8_t *d, int len) { return ttf_open(&T, d, len); }
int zt_glyph(int cp) { return ttf_glyph_index(&T, cp); }
int zt_advance(int g) { return ttf_advance(&T, g); }
int zt_units(void) { return T.unitsPerEm; }
int zt_ascent(void) { return T.ascent; }
int zt_descent(void) { return T.descent; }
int zt_gap(void) { return T.lineGap; }
int zt_raster(int g, double px, double sub, int *w, int *h, int *left, int *top, uint8_t *buf, int cap) {
    GlyphBitmap b;
    if (!ttf_raster(&T, g, px, sub, &b)) return 0;
    *w = b.w; *h = b.h; *left = b.left; *top = b.top;
    if (b.px) { if (b.w * b.h <= cap) memcpy(buf, b.px, (size_t)b.w * b.h); free(b.px); }
    return 1;
}
#include "zf_gpos.h"
int zt_kern(int a, int b) { return ttf_kern(&T, a, b); }
