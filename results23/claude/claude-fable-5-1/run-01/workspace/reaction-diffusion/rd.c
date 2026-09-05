/*
 * rd.c — Gray-Scott reaction-diffusion, rendered to PNG with zero dependencies.
 *
 * Two chemicals U and V live on a toroidal grid. U is fed in, V is removed,
 * and U + 2V -> 3V. Depending on feed (F) and kill (k) rates the system settles
 * into spots, stripes, mazes, or dividing "cells".
 *
 *   build: cc -O2 -o rd rd.c -lm
 *   usage: ./rd [preset] [steps] [out.png]
 *          presets: coral mitosis maze worms spots
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

#define W 512
#define H 512

static float U[2][H][W], V[2][H][W];

/* ---------- PNG writer (stored deflate, no zlib) ---------- */

static uint32_t crc_table[256];
static void crc_init(void) {
    for (uint32_t n = 0; n < 256; n++) {
        uint32_t c = n;
        for (int k = 0; k < 8; k++) c = (c & 1) ? 0xEDB88320u ^ (c >> 1) : c >> 1;
        crc_table[n] = c;
    }
}
static uint32_t crc_update(uint32_t c, const uint8_t *p, size_t n) {
    c ^= 0xFFFFFFFFu;
    while (n--) c = crc_table[(c ^ *p++) & 0xFF] ^ (c >> 8);
    return c ^ 0xFFFFFFFFu;
}
static void put32(FILE *f, uint32_t v) {
    uint8_t b[4] = { v >> 24, v >> 16, v >> 8, v };
    fwrite(b, 1, 4, f);
}
static void chunk(FILE *f, const char *type, const uint8_t *data, size_t len) {
    put32(f, (uint32_t)len);
    uint32_t c = crc_update(0, (const uint8_t *)type, 4);
    fwrite(type, 1, 4, f);
    if (len) { fwrite(data, 1, len, f); c = crc_update(c, data, len); }
    put32(f, c);
}

/* raw = filtered scanlines (each row prefixed with filter byte 0) */
static void write_png(const char *path, const uint8_t *rgb, int w, int h) {
    size_t rowlen = 1 + (size_t)w * 3;
    size_t rawlen = rowlen * h;
    uint8_t *raw = malloc(rawlen);
    for (int y = 0; y < h; y++) {
        raw[y * rowlen] = 0;
        memcpy(raw + y * rowlen + 1, rgb + (size_t)y * w * 3, (size_t)w * 3);
    }

    /* zlib stream: header, stored blocks of <= 65535 bytes, adler32 */
    size_t nblocks = (rawlen + 65534) / 65535;
    size_t zlen = 2 + rawlen + nblocks * 5 + 4;
    uint8_t *z = malloc(zlen);
    size_t zi = 0;
    z[zi++] = 0x78; z[zi++] = 0x01;
    uint32_t a = 1, b = 0;
    for (size_t off = 0; off < rawlen; off += 65535) {
        size_t n = rawlen - off < 65535 ? rawlen - off : 65535;
        int final = (off + n == rawlen);
        z[zi++] = (uint8_t)final;
        z[zi++] = n & 0xFF; z[zi++] = n >> 8;
        z[zi++] = ~n & 0xFF; z[zi++] = (~n >> 8) & 0xFF;
        memcpy(z + zi, raw + off, n);
        for (size_t i = 0; i < n; i++) { a = (a + raw[off + i]) % 65521; b = (b + a) % 65521; }
        zi += n;
    }
    uint32_t adler = (b << 16) | a;
    z[zi++] = adler >> 24; z[zi++] = adler >> 16; z[zi++] = adler >> 8; z[zi++] = adler;

    FILE *f = fopen(path, "wb");
    if (!f) { perror(path); exit(1); }
    static const uint8_t sig[8] = { 137, 80, 78, 71, 13, 10, 26, 10 };
    fwrite(sig, 1, 8, f);
    uint8_t ihdr[13] = { w >> 24, w >> 16, w >> 8, w, h >> 24, h >> 16, h >> 8, h, 8, 2, 0, 0, 0 };
    chunk(f, "IHDR", ihdr, 13);
    chunk(f, "IDAT", z, zi);
    chunk(f, "IEND", NULL, 0);
    fclose(f);
    free(raw); free(z);
}

/* ---------- simulation ---------- */

typedef struct { const char *name; float F, k; } Preset;
static const Preset presets[] = {
    { "coral",   0.0545f, 0.0620f },
    { "mitosis", 0.0367f, 0.0649f },
    { "maze",    0.0290f, 0.0570f },
    { "worms",   0.0580f, 0.0650f },
    { "spots",   0.0300f, 0.0620f },
};

static inline int wrap(int i, int n) { return i < 0 ? i + n : (i >= n ? i - n : i); }

static void step(int src, float F, float k) {
    const float Du = 1.0f, Dv = 0.5f;
    int dst = 1 - src;
    for (int y = 0; y < H; y++) {
        int ym = wrap(y - 1, H), yp = wrap(y + 1, H);
        for (int x = 0; x < W; x++) {
            int xm = wrap(x - 1, W), xp = wrap(x + 1, W);
            float u = U[src][y][x], v = V[src][y][x];
            /* 9-point Laplacian: centre -1, edges .2, corners .05 */
            float lu = -u
                + 0.20f * (U[src][ym][x] + U[src][yp][x] + U[src][y][xm] + U[src][y][xp])
                + 0.05f * (U[src][ym][xm] + U[src][ym][xp] + U[src][yp][xm] + U[src][yp][xp]);
            float lv = -v
                + 0.20f * (V[src][ym][x] + V[src][yp][x] + V[src][y][xm] + V[src][y][xp])
                + 0.05f * (V[src][ym][xm] + V[src][ym][xp] + V[src][yp][xm] + V[src][yp][xp]);
            float uvv = u * v * v;
            U[dst][y][x] = u + Du * lu - uvv + F * (1.0f - u);
            V[dst][y][x] = v + Dv * lv + uvv - (F + k) * v;
        }
    }
}

/* smooth dark-teal -> amber -> cream ramp */
static void colour(float t, uint8_t *out) {
    if (t < 0) t = 0;
    if (t > 1) t = 1;
    static const float stops[5][3] = {
        { 0.04f, 0.05f, 0.10f },   /* near-black navy */
        { 0.05f, 0.30f, 0.38f },   /* deep teal */
        { 0.85f, 0.45f, 0.10f },   /* amber */
        { 0.98f, 0.82f, 0.45f },   /* gold */
        { 1.00f, 0.97f, 0.90f },   /* cream */
    };
    float p = t * 4.0f; int i = (int)p; if (i > 3) i = 3; float f = p - i;
    for (int c = 0; c < 3; c++)
        out[c] = (uint8_t)(255.0f * (stops[i][c] + (stops[i + 1][c] - stops[i][c]) * f) + 0.5f);
}

int main(int argc, char **argv) {
    const Preset *P = &presets[0];
    int steps = 10000;
    const char *out = "rd.png";
    if (argc > 1) {
        P = NULL;
        for (size_t i = 0; i < sizeof presets / sizeof *presets; i++)
            if (!strcmp(argv[1], presets[i].name)) P = &presets[i];
        if (!P) { fprintf(stderr, "unknown preset %s\n", argv[1]); return 1; }
    }
    if (argc > 2) steps = atoi(argv[2]);
    if (argc > 3) out = argv[3];

    srand(1234);
    for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) { U[0][y][x] = 1.0f; V[0][y][x] = 0.0f; }
    /* seed with a scattering of small V-rich squares */
    for (int s = 0; s < 24; s++) {
        int cx = rand() % W, cy = rand() % H, r = 4 + rand() % 8;
        for (int dy = -r; dy <= r; dy++) for (int dx = -r; dx <= r; dx++) {
            int x = wrap(cx + dx, W), y = wrap(cy + dy, H);
            U[0][y][x] = 0.50f; V[0][y][x] = 0.25f;
        }
    }

    int cur = 0;
    for (int i = 0; i < steps; i++) { step(cur, P->F, P->k); cur = 1 - cur; }

    /* normalise V for display */
    float vmin = 1e9f, vmax = -1e9f;
    for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) {
        float v = V[cur][y][x]; if (v < vmin) vmin = v; if (v > vmax) vmax = v;
    }
    uint8_t *rgb = malloc((size_t)W * H * 3);
    for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) {
        float t = (V[cur][y][x] - vmin) / (vmax - vmin + 1e-9f);
        colour(sqrtf(t), rgb + ((size_t)y * W + x) * 3);
    }
    crc_init();
    write_png(out, rgb, W, H);
    free(rgb);
    printf("%s: F=%.4f k=%.4f, %d steps, V in [%.4f, %.4f] -> %s\n",
           P->name, P->F, P->k, steps, vmin, vmax, out);
    return 0;
}
