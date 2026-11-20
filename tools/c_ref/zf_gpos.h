/* zf_gpos.h — the C twin of src/text/kern.axle: pair kerning from GPOS.
 *
 * Only what a UI face needs: the `kern` feature's PairPos lookups (format 1 glyph pairs and
 * format 2 class pairs), reached directly or through an Extension lookup. No script or language
 * selection, no contextual lookups, no mark positioning. The answer is the first glyph's
 * XAdvance adjustment, in font units.
 */
#ifndef ZF_GPOS_H
#define ZF_GPOS_H
#include "zf_ttf.h"

/* Index of glyph g in the coverage table at `off`, or -1. */
static int gpos_coverage(const Ttf *t, int off, int g) {
    int fmt = zf_u16(t, off), n = zf_u16(t, off + 2);
    if (fmt == 1) {
        int lo = 0, hi = n - 1;
        while (lo <= hi) {
            int mid = (lo + hi) / 2, v = zf_u16(t, off + 4 + mid * 2);
            if (v == g) return mid;
            if (v < g) lo = mid + 1; else hi = mid - 1;
        }
        return -1;
    }
    if (fmt == 2) {
        int lo = 0, hi = n - 1;
        while (lo <= hi) {
            int mid = (lo + hi) / 2, r = off + 4 + mid * 6;
            int s = zf_u16(t, r), e = zf_u16(t, r + 2);
            if (g < s) hi = mid - 1;
            else if (g > e) lo = mid + 1;
            else return zf_u16(t, r + 4) + (g - s);
        }
    }
    return -1;
}

static int gpos_class(const Ttf *t, int off, int g) {
    int fmt = zf_u16(t, off);
    if (fmt == 1) {
        int start = zf_u16(t, off + 2), n = zf_u16(t, off + 4);
        return (g >= start && g < start + n) ? zf_u16(t, off + 6 + (g - start) * 2) : 0;
    }
    if (fmt == 2) {
        int n = zf_u16(t, off + 2), lo = 0, hi = n - 1;
        while (lo <= hi) {
            int mid = (lo + hi) / 2, r = off + 4 + mid * 6;
            int s = zf_u16(t, r), e = zf_u16(t, r + 2);
            if (g < s) hi = mid - 1;
            else if (g > e) lo = mid + 1;
            else return zf_u16(t, r + 4);
        }
    }
    return 0;
}

static int gpos_popcount(int v) { int c = 0; while (v) { c += v & 1; v >>= 1; } return c; }

/* The XAdvance of a value record of `fmt` at `off`, or 0 when the format has none. */
static int gpos_xadv(const Ttf *t, int off, int fmt) {
    if (!(fmt & 4)) return 0;
    return zf_i16(t, off + gpos_popcount(fmt & 3) * 2);
}

/* 1 and *out set when this PairPos subtable applies to (a, b). */
static int gpos_pair_sub(const Ttf *t, int sub, int a, int b, int *out) {
    int fmt = zf_u16(t, sub);
    int ci = gpos_coverage(t, sub + zf_u16(t, sub + 2), a);
    if (ci < 0) return 0;
    int vf1 = zf_u16(t, sub + 4), vf2 = zf_u16(t, sub + 6);
    int s1 = gpos_popcount(vf1) * 2, s2 = gpos_popcount(vf2) * 2;
    if (fmt == 1) {
        int set = sub + zf_u16(t, sub + 10 + ci * 2), n = zf_u16(t, set);
        int rec = s1 + s2 + 2;
        int lo = 0, hi = n - 1;
        while (lo <= hi) {
            int mid = (lo + hi) / 2, r = set + 2 + mid * rec, sg = zf_u16(t, r);
            if (sg == b) { *out = gpos_xadv(t, r + 2, vf1); return 1; }
            if (sg < b) lo = mid + 1; else hi = mid - 1;
        }
        return 0;
    }
    if (fmt == 2) {
        int c1 = gpos_class(t, sub + zf_u16(t, sub + 8), a);
        int c2 = gpos_class(t, sub + zf_u16(t, sub + 10), b);
        int n1 = zf_u16(t, sub + 12), n2 = zf_u16(t, sub + 14);
        if (c1 >= n1 || c2 >= n2) return 0;
        int rec = s1 + s2;
        *out = gpos_xadv(t, sub + 16 + (c1 * n2 + c2) * rec, vf1);
        return 1;
    }
    return 0;
}

/* Kerning between glyphs a and b, in font units; 0 when the font has none. */
static int ttf_kern(const Ttf *t, int a, int b) {
    if (!t->gpos) return 0;
    int g = t->gpos;
    int feats = g + zf_u16(t, g + 6), lookups = g + zf_u16(t, g + 8);
    int nf = zf_u16(t, feats);
    for (int i = 0; i < nf; i++) {
        int rec = feats + 2 + i * 6;
        if (memcmp(t->d + rec, "kern", 4) != 0) continue;
        int ft = feats + zf_u16(t, rec + 4), nl = zf_u16(t, ft + 2);
        for (int k = 0; k < nl; k++) {
            int li = zf_u16(t, ft + 4 + k * 2);
            int lk = lookups + zf_u16(t, lookups + 2 + li * 2);
            int type = zf_u16(t, lk), ns = zf_u16(t, lk + 4);
            for (int s = 0; s < ns; s++) {
                int sub = lk + zf_u16(t, lk + 6 + s * 2), st = type;
                if (type == 9) {
                    st = zf_u16(t, sub + 2);
                    sub = sub + (int)zf_u32(t, sub + 4);
                }
                if (st != 2) continue;
                int v;
                if (gpos_pair_sub(t, sub, a, b, &v)) return v;
            }
        }
    }
    return 0;
}
#endif
