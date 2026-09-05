/* trace.c — a small self-contained ray tracer.
 *
 * Renders a scene of glossy spheres on a checkerboard plane with
 * recursive reflections, soft shadows from an area light, and a
 * gradient sky, then writes a PNG with zero dependencies (the PNG
 * uses stored/uncompressed deflate blocks, so only CRC32 and
 * Adler32 need implementing).
 *
 * Build:  gcc -O2 -o trace trace.c -lm
 * Run:    ./trace out.png
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>

/* ---------- vec3 ---------- */
typedef struct { double x, y, z; } v3;
static v3 V(double x, double y, double z){ v3 r={x,y,z}; return r; }
static v3 add(v3 a, v3 b){ return V(a.x+b.x, a.y+b.y, a.z+b.z); }
static v3 sub(v3 a, v3 b){ return V(a.x-b.x, a.y-b.y, a.z-b.z); }
static v3 mul(v3 a, double s){ return V(a.x*s, a.y*s, a.z*s); }
static v3 hadamard(v3 a, v3 b){ return V(a.x*b.x, a.y*b.y, a.z*b.z); }
static double dot(v3 a, v3 b){ return a.x*b.x + a.y*b.y + a.z*b.z; }
static v3 norm(v3 a){ double l = sqrt(dot(a,a)); return mul(a, 1.0/l); }
static v3 reflect(v3 d, v3 n){ return sub(d, mul(n, 2.0*dot(d,n))); }

/* xorshift RNG for jittered sampling */
static uint64_t rng_state = 0x9e3779b97f4a7c15ULL;
static double frand(void){
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return (double)(rng_state >> 11) / 9007199254740992.0;
}

/* ---------- scene ---------- */
typedef struct {
    v3 center; double radius;
    v3 color;
    double reflectivity;   /* 0..1 mirror mix */
    double specular;       /* phong exponent */
} sphere;

static sphere spheres[] = {
    { { 0.0, 1.0,  0.0}, 1.00, {0.85, 0.25, 0.20}, 0.22, 220.0 }, /* red, center   */
    { {-2.2, 0.7,  1.2}, 0.70, {0.20, 0.45, 0.85}, 0.25, 120.0 }, /* blue, left    */
    { { 2.1, 0.6, -0.4}, 0.60, {0.95, 0.75, 0.15}, 0.20,  60.0 }, /* gold, right   */
    { { 0.9, 0.4,  2.0}, 0.40, {0.90, 0.90, 0.92}, 0.85, 500.0 }, /* mirror, front */
    { {-1.0, 0.3,  2.6}, 0.30, {0.30, 0.75, 0.40}, 0.15,  40.0 }, /* green, front  */
};
#define NSPHERES ((int)(sizeof(spheres)/sizeof(spheres[0])))

/* area light: a disc, sampled for soft shadows */
static const v3 LIGHT_POS = { -4.5, 6.0, 3.5 };
static const double LIGHT_RADIUS = 1.4;
static const v3 LIGHT_COLOR = { 1.0, 0.97, 0.9 };
static const double LIGHT_INTENSITY = 1.35;

static const double AMBIENT = 0.12;
static const int MAX_DEPTH = 5;
static const int SHADOW_SAMPLES = 12;

/* ---------- intersection ---------- */
static double hit_sphere(const sphere *s, v3 o, v3 d){
    v3 oc = sub(o, s->center);
    double b = dot(oc, d);
    double c = dot(oc, oc) - s->radius * s->radius;
    double disc = b*b - c;
    if (disc < 0) return -1.0;
    double sq = sqrt(disc);
    double t = -b - sq;
    if (t > 1e-4) return t;
    t = -b + sq;
    if (t > 1e-4) return t;
    return -1.0;
}

/* plane y=0 */
static double hit_floor(v3 o, v3 d){
    if (fabs(d.y) < 1e-9) return -1.0;
    double t = -o.y / d.y;
    return (t > 1e-4) ? t : -1.0;
}

/* nearest hit: returns t, sets *id (sphere index, or -1 for floor, -2 for miss) */
static double intersect(v3 o, v3 d, int *id){
    double best = 1e30; *id = -2;
    for (int i = 0; i < NSPHERES; i++){
        double t = hit_sphere(&spheres[i], o, d);
        if (t > 0 && t < best){ best = t; *id = i; }
    }
    double tf = hit_floor(o, d);
    if (tf > 0 && tf < best){ best = tf; *id = -1; }
    return best;
}

/* fraction of the area light visible from p (soft shadow) */
static double light_visibility(v3 p){
    /* build a basis on the light disc */
    v3 to_light = norm(sub(LIGHT_POS, p));
    v3 up = fabs(to_light.y) < 0.9 ? V(0,1,0) : V(1,0,0);
    v3 u = norm(V(to_light.y*up.z - to_light.z*up.y,
                  to_light.z*up.x - to_light.x*up.z,
                  to_light.x*up.y - to_light.y*up.x));
    v3 v = V(to_light.y*u.z - to_light.z*u.y,
             to_light.z*u.x - to_light.x*u.z,
             to_light.x*u.y - to_light.y*u.x);
    int visible = 0;
    for (int i = 0; i < SHADOW_SAMPLES; i++){
        double ang = 2.0 * M_PI * frand();
        double rad = LIGHT_RADIUS * sqrt(frand());
        v3 lp = add(LIGHT_POS, add(mul(u, cos(ang)*rad), mul(v, sin(ang)*rad)));
        v3 dir = sub(lp, p);
        double dist = sqrt(dot(dir, dir));
        dir = mul(dir, 1.0/dist);
        int id; double t = intersect(p, dir, &id);
        if (id == -2 || t > dist) visible++;
    }
    return (double)visible / SHADOW_SAMPLES;
}

static v3 sky(v3 d){
    double t = 0.5 * (d.y + 1.0);
    v3 horizon = V(0.95, 0.85, 0.75);
    v3 zenith  = V(0.35, 0.55, 0.90);
    return add(mul(horizon, 1.0 - t), mul(zenith, t));
}

static v3 shade(v3 o, v3 d, int depth);

static v3 surface_color(v3 p, v3 n, v3 d, v3 base, double refl, double spec, int depth){
    v3 to_light = norm(sub(LIGHT_POS, p));
    double vis = light_visibility(p);
    double diff = fmax(0.0, dot(n, to_light)) * vis * LIGHT_INTENSITY;
    v3 col = mul(hadamard(base, LIGHT_COLOR), AMBIENT + diff);

    /* phong highlight */
    if (spec > 0 && vis > 0){
        v3 h = norm(sub(to_light, d));
        double s = pow(fmax(0.0, dot(n, h)), spec) * vis * LIGHT_INTENSITY;
        col = add(col, mul(LIGHT_COLOR, s * 0.6));
    }
    /* reflection */
    if (refl > 0 && depth < MAX_DEPTH){
        v3 r = shade(p, norm(reflect(d, n)), depth + 1);
        col = add(mul(col, 1.0 - refl), mul(r, refl));
    }
    return col;
}

static v3 shade(v3 o, v3 d, int depth){
    int id;
    double t = intersect(o, d, &id);
    if (id == -2) return sky(d);
    v3 p = add(o, mul(d, t));

    if (id == -1){
        /* checkerboard floor */
        int check = ((int)floor(p.x + 0.5) + (int)floor(p.z + 0.5)) & 1;
        v3 base = check ? V(0.92, 0.92, 0.9) : V(0.18, 0.18, 0.2);
        /* fade the floor to sky color in the distance */
        v3 col = surface_color(p, V(0,1,0), d, base, 0.22, 0.0, depth);
        double fog = fmin(1.0, t / 45.0);
        return add(mul(col, 1.0 - fog), mul(sky(d), fog));
    }
    const sphere *s = &spheres[id];
    v3 n = norm(sub(p, s->center));
    return surface_color(p, n, d, s->color, s->reflectivity, s->specular, depth);
}

/* ---------- PNG writer (stored deflate, no libs) ---------- */
static uint32_t crc_table[256];
static void crc_init(void){
    for (uint32_t n = 0; n < 256; n++){
        uint32_t c = n;
        for (int k = 0; k < 8; k++)
            c = (c & 1) ? 0xedb88320u ^ (c >> 1) : c >> 1;
        crc_table[n] = c;
    }
}
static uint32_t crc32_buf(uint32_t crc, const uint8_t *buf, size_t len){
    crc = ~crc;
    for (size_t i = 0; i < len; i++)
        crc = crc_table[(crc ^ buf[i]) & 0xff] ^ (crc >> 8);
    return ~crc;
}
static void be32(uint8_t *p, uint32_t v){
    p[0]=v>>24; p[1]=v>>16; p[2]=v>>8; p[3]=v;
}
static void chunk(FILE *f, const char *type, const uint8_t *data, uint32_t len){
    uint8_t hdr[8];
    be32(hdr, len);
    memcpy(hdr+4, type, 4);
    fwrite(hdr, 1, 8, f);
    if (len) fwrite(data, 1, len, f);
    uint32_t crc = crc32_buf(0, hdr+4, 4);
    crc = crc32_buf(crc, data, len);
    uint8_t tail[4]; be32(tail, crc);
    fwrite(tail, 1, 4, f);
}
static void write_png(const char *path, const uint8_t *rgb, int w, int h){
    crc_init();
    FILE *f = fopen(path, "wb");
    if (!f){ perror(path); exit(1); }
    const uint8_t sig[8] = {137,80,78,71,13,10,26,10};
    fwrite(sig, 1, 8, f);

    uint8_t ihdr[13];
    be32(ihdr, (uint32_t)w); be32(ihdr+4, (uint32_t)h);
    ihdr[8]=8; ihdr[9]=2; ihdr[10]=0; ihdr[11]=0; ihdr[12]=0; /* 8-bit RGB */
    chunk(f, "IHDR", ihdr, 13);

    /* raw scanlines: filter byte 0 + w*3 bytes each */
    size_t rowlen = 1 + (size_t)w*3;
    size_t rawlen = rowlen * h;
    uint8_t *raw = malloc(rawlen);
    for (int y = 0; y < h; y++){
        raw[y*rowlen] = 0;
        memcpy(raw + y*rowlen + 1, rgb + (size_t)y*w*3, (size_t)w*3);
    }
    /* zlib stream with stored deflate blocks (max 65535 bytes each) */
    size_t nblocks = (rawlen + 65534) / 65535;
    size_t zlen = 2 + rawlen + nblocks*5 + 4;
    uint8_t *z = malloc(zlen);
    size_t zi = 0;
    z[zi++] = 0x78; z[zi++] = 0x01; /* zlib header, no dict */
    size_t off = 0;
    while (off < rawlen){
        size_t n = rawlen - off; if (n > 65535) n = 65535;
        z[zi++] = (off + n == rawlen) ? 1 : 0; /* BFINAL */
        z[zi++] = n & 0xff; z[zi++] = n >> 8;
        z[zi++] = ~n & 0xff; z[zi++] = (~n >> 8) & 0xff;
        memcpy(z + zi, raw + off, n);
        zi += n; off += n;
    }
    /* adler32 of raw data */
    uint32_t a = 1, b = 0;
    for (size_t i = 0; i < rawlen; i++){
        a = (a + raw[i]) % 65521;
        b = (b + a) % 65521;
    }
    be32(z + zi, (b << 16) | a); zi += 4;
    chunk(f, "IDAT", z, (uint32_t)zi);
    chunk(f, "IEND", NULL, 0);
    fclose(f);
    free(raw); free(z);
}

/* ---------- main ---------- */
int main(int argc, char **argv){
    const char *out = argc > 1 ? argv[1] : "out.png";
    const int W = 1280, H = 800, SPP = 16; /* 4x4 jittered supersampling */

    v3 cam = V(0.0, 1.8, 6.5);
    v3 look = V(0.0, 0.8, 0.0);
    v3 fwd = norm(sub(look, cam));
    v3 right = norm(V(-fwd.z, 0, fwd.x)); /* fwd x worldUp */
    v3 up = V(right.y*fwd.z - right.z*fwd.y,
              right.z*fwd.x - right.x*fwd.z,
              right.x*fwd.y - right.y*fwd.x);
    double fov = 0.9; /* ~52 deg vertical */
    double aspect = (double)W / H;

    uint8_t *img = malloc((size_t)W*H*3);
    for (int y = 0; y < H; y++){
        for (int x = 0; x < W; x++){
            v3 acc = V(0,0,0);
            for (int s = 0; s < SPP; s++){
                double jx = ((s & 3) + frand()) * 0.25;   /* 4x4 stratified grid */
                double jy = ((s >> 2) + frand()) * 0.25;
                double u = ((x + jx) / W * 2.0 - 1.0) * tan(fov/2) * aspect;
                double v = (1.0 - (y + jy) / H * 2.0) * tan(fov/2);
                v3 d = norm(add(fwd, add(mul(right, u), mul(up, v))));
                acc = add(acc, shade(cam, d, 0));
            }
            acc = mul(acc, 1.0 / SPP);
            uint8_t *px = img + ((size_t)y*W + x)*3;
            /* gamma 2.2 and clamp */
            px[0] = (uint8_t)(255.0 * fmin(1.0, pow(fmax(0.0, acc.x), 1/2.2)));
            px[1] = (uint8_t)(255.0 * fmin(1.0, pow(fmax(0.0, acc.y), 1/2.2)));
            px[2] = (uint8_t)(255.0 * fmin(1.0, pow(fmax(0.0, acc.z), 1/2.2)));
        }
        if (y % 60 == 0) fprintf(stderr, "row %d/%d\n", y, H);
    }
    write_png(out, img, W, H);
    free(img);
    fprintf(stderr, "wrote %s (%dx%d)\n", out, W, H);
    return 0;
}
