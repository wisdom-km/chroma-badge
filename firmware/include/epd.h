#pragma once

#include <cstdint>

/* GDEM042F86 / SSD2683ZA, 400x300, 2 bit/pixel BWRY.
 * Init sequence: official spec 2026-06-17 section 10.2 (LUT from OTP). */

namespace epd {

constexpr int WIDTH = 400;
constexpr int HEIGHT = 300;
constexpr int FRAME_BYTES = WIDTH * HEIGHT / 4;  // 2 bpp packed, 4 px/byte

enum class Color : uint8_t {
    Black  = 0b00,
    White  = 0b01,
    Yellow = 0b10,
    Red    = 0b11,
};

void begin();
void power_on();
void power_off();
bool refresh_solid(Color color);  // OTP full update, then panel deep-sleep + rail off

}  // namespace epd
