/* test_gfx.c — draws the shapes the Axle `Canvas` draws, so they can be looked at, and asserts
 * the properties that should hold whatever they look like. Writes build/gfx.ppm. */
#include <assert.h>
#include <stdio.h>
#include "zf_gfx.h"

#define W 640
#define H 420
static uint32_t buf[W * H];

static void fill_all(Canvas *c, uint32_t rgb) { for (int i = 0; i < c->w * c->h; i++) c->px[i] = rgb; }

int main(void) {
    Canvas c = { buf, W, H, 0, 0, W, H, 255 };
    fill_all(&c, 0x0E1015);

    /* a card with a soft shadow and a hairline border */
    RRect card = zf_rrect_u(30, 30, 280, 170, 14);
    zf_shadow(&c, &card, 0, 8, 24, -2, 0x000000, 150);
    zf_shadow(&c, &card, 0, 1, 3, 0, 0x000000, 90);
    Brush fillc = zf_solid(0x161920, 255);
    zf_shape(&c, &card, 0, &fillc);
    Brush edge = zf_solid(0x272C37, 255);
    zf_shape(&c, &card, 1.0, &edge);

    /* primary button: vertical gradient + inner highlight line */
    RRect b1 = zf_rrect_u(54, 64, 120, 38, 10);
    Brush g1 = zf_linear(0x8EA0FF, 255, 0x6577F5, 255, 0, 64, 0, 102);
    zf_shadow(&c, &b1, 0, 4, 10, 0, 0x4A5CE0, 110);
    zf_shape(&c, &b1, 0, &g1);
    Brush hi = zf_solid(0xFFFFFF, 46);
    RRect b1i = zf_rrect_u(54.5, 64.5, 119, 37, 9.5);
    zf_shape(&c, &b1i, 1.0, &hi);

    /* ghost / outline buttons */
    RRect b2 = zf_rrect_u(188, 64, 100, 38, 10);
    Brush e2 = zf_solid(0x3A4152, 255);
    zf_shape(&c, &b2, 1.0, &e2);

    /* pill + chip */
    RRect pill = zf_rrect_u(54, 120, 84, 24, 12);
    Brush pc = zf_solid(0x1E2742, 255);
    zf_shape(&c, &pill, 0, &pc);
    Brush pe = zf_solid(0x7A8CFF, 120);
    zf_shape(&c, &pill, 1.0, &pe);

    /* switch on / off */
    RRect sw = zf_rrect_u(160, 122, 44, 24, 12);
    Brush on = zf_linear(0x7A8CFF, 255, 0x6070F0, 255, 0, 122, 0, 146);
    zf_shape(&c, &sw, 0, &on);
    RRect knob = zf_rrect_u(184, 125, 18, 18, 9);
    zf_shadow(&c, &knob, 0, 1, 3, 0, 0x000000, 120);
    Brush white = zf_solid(0xFFFFFF, 255);
    zf_shape(&c, &knob, 0, &white);
    RRect sw2 = zf_rrect_u(220, 122, 44, 24, 12);
    Brush off = zf_solid(0x2A3040, 255);
    zf_shape(&c, &sw2, 0, &off);
    RRect knob2 = zf_rrect_u(223, 125, 18, 18, 9);
    Brush dim = zf_solid(0x9AA3B5, 255);
    zf_shape(&c, &knob2, 0, &dim);

    /* a slider */
    RRect track = zf_rrect_u(54, 170, 210, 6, 3);
    zf_shape(&c, &track, 0, &off);
    RRect fillt = zf_rrect_u(54, 170, 120, 6, 3);
    zf_shape(&c, &fillt, 0, &on);
    RRect thumb = zf_rrect_u(165, 164, 18, 18, 9);
    zf_shadow(&c, &thumb, 0, 1, 4, 0, 0x000000, 140);
    zf_shape(&c, &thumb, 0, &white);

    /* per-corner radii (a tab, a toast) and a capsule check mark */
    RRect tab = zf_rrect(340, 40, 120, 40, 12, 12, 0, 0);
    zf_shape(&c, &tab, 0, &fillc);
    zf_shape(&c, &tab, 1.0, &edge);
    zf_capsule(&c, 360, 130, 368, 138, 2.0, 0x3DD68C, 255);
    zf_capsule(&c, 368, 138, 382, 120, 2.0, 0x3DD68C, 255);

    /* light theme sample */
    Canvas lt = c; lt.cx0 = 340; lt.cy0 = 200; lt.cx1 = 620; lt.cy1 = 400;
    for (int y = 200; y < 400; y++) for (int x = 340; x < 620; x++) buf[y * W + x] = 0xF4F5F8;
    RRect lc = zf_rrect_u(360, 220, 240, 150, 14);
    zf_shadow(&lt, &lc, 0, 10, 28, -4, 0x1E2A50, 60);
    zf_shadow(&lt, &lc, 0, 1, 2, 0, 0x1E2A50, 36);
    Brush lw = zf_solid(0xFFFFFF, 255);
    zf_shape(&lt, &lc, 0, &lw);
    Brush le = zf_solid(0xE3E6EE, 255);
    zf_shape(&lt, &lc, 1.0, &le);
    RRect lb = zf_rrect_u(380, 240, 110, 36, 10);
    Brush lg = zf_linear(0x6B7CFF, 255, 0x5565F0, 255, 0, 240, 0, 276);
    zf_shape(&lt, &lb, 0, &lg);

    /* properties */
    assert(zf_div255(255 * 255) == 255 && zf_div255(0) == 0 && zf_div255(128 * 255) == 128);
    assert(zf_over(0x000000, 0xFFFFFF, 128) == 0x808080);
    RRect u = zf_rrect_u(0, 0, 10, 10, 5);
    assert(zf_sdf(&u, 5, 5) == -5.0);
    assert(fabs(zf_sdf(&u, 5, 0) - 0.0) < 1e-9);
    /* a filled integer-aligned rect is exactly opaque inside and empty outside */
    uint32_t t[16 * 16]; memset(t, 0, sizeof t);
    Canvas tc = { t, 16, 16, 0, 0, 16, 16, 255 };
    RRect sq = zf_rrect_u(4, 4, 8, 8, 0);
    Brush wb = zf_solid(0xFFFFFF, 255);
    zf_shape(&tc, &sq, 0, &wb);
    for (int y = 0; y < 16; y++) for (int x = 0; x < 16; x++)
        assert(t[y * 16 + x] == ((x >= 4 && x < 12 && y >= 4 && y < 12) ? 0xFFFFFFu : 0u));

    FILE *f = fopen("build/gfx.ppm", "wb");
    fprintf(f, "P6\n%d %d\n255\n", W, H);
    for (int i = 0; i < W * H; i++) { fputc((buf[i] >> 16) & 255, f); fputc((buf[i] >> 8) & 255, f); fputc(buf[i] & 255, f); }
    fclose(f);
    puts("test_gfx: ok");
    return 0;
}
