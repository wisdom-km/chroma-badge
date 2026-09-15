#include "epd.h"

#include "pins.h"

#include <Arduino.h>
#include <SPI.h>

namespace epd {
namespace {

SPIClass *spi = &SPI;

void cs(bool level) { digitalWrite(pins::EPD_CS, level); }
void dc(bool level) { digitalWrite(pins::EPD_DC, level); }

void send_byte(uint8_t b) { spi->transfer(b); }

void cmd(uint8_t c) {
    dc(LOW);
    cs(LOW);
    send_byte(c);
    cs(HIGH);
}

void data(uint8_t d) {
    dc(HIGH);
    cs(LOW);
    send_byte(d);
    cs(HIGH);
}

void cmd_data(uint8_t c, const uint8_t *d, size_t n) {
    dc(LOW);
    cs(LOW);
    send_byte(c);
    dc(HIGH);
    for (size_t i = 0; i < n; i++) {
        send_byte(d[i]);
    }
    cs(HIGH);
}

}  // namespace

const char *last_fail = "";

namespace {

bool wait_busy_cycle(uint32_t timeout_ms, const char *stage) {
    // After a command the panel must go BUSY (LOW) then idle (HIGH).
    // Stuck HIGH (no panel / floating) used to return true immediately.
    uint32_t t0 = millis();
    if (digitalRead(pins::EPD_BUSY) == HIGH) {
        while (digitalRead(pins::EPD_BUSY) == HIGH) {
            if (millis() - t0 > timeout_ms) {
                if (!last_fail[0]) {
                    last_fail = stage;
                }
                return false;
            }
            delay(2);
        }
    }
    while (digitalRead(pins::EPD_BUSY) == LOW) {
        if (millis() - t0 > timeout_ms) {
            if (!last_fail[0]) {
                last_fail = stage;
            }
            return false;
        }
        delay(2);
    }
    return true;
}

void hw_reset() {
    digitalWrite(pins::EPD_RST, HIGH);
    delay(10);
    digitalWrite(pins::EPD_RST, LOW);
    delay(10);
    digitalWrite(pins::EPD_RST, HIGH);
    delay(10);
}

void init_otp() {
    // GDEM042F86 spec p.31 — LUT from OTP
    const uint8_t psr[]  = {0x2F, 0x69};
    const uint8_t btst[] = {0x0F, 0x8B, 0x9C, 0x96};
    const uint8_t pwr[]  = {0x07, 0xF0};
    const uint8_t cdi[]  = {0x37};
    const uint8_t tres[] = {0x01, 0x90, 0x01, 0x2C};  // 400 x 300
    const uint8_t r62[]  = {0x64, 0x53};
    const uint8_t gsst[] = {0x00, 0x00, 0x00, 0x00};
    const uint8_t pll[]  = {0x08};
    const uint8_t e9[]   = {0x01};
    cmd_data(0x00, psr, sizeof(psr));
    cmd_data(0x06, btst, sizeof(btst));
    cmd_data(0x01, pwr, sizeof(pwr));
    cmd_data(0x50, cdi, sizeof(cdi));
    cmd_data(0x61, tres, sizeof(tres));
    cmd_data(0x62, r62, sizeof(r62));
    cmd_data(0x65, gsst, sizeof(gsst));
    cmd_data(0x30, pll, sizeof(pll));
    cmd_data(0xE9, e9, sizeof(e9));
}

void spi_idle_low() {
    digitalWrite(pins::EPD_CS, LOW);
    digitalWrite(pins::EPD_DC, LOW);
    digitalWrite(pins::EPD_RST, LOW);
    digitalWrite(pins::EPD_SCK, LOW);
    digitalWrite(pins::EPD_MOSI, LOW);
}

}  // namespace

void begin() {
    pinMode(pins::EPD_PWR_EN, OUTPUT);
    digitalWrite(pins::EPD_PWR_EN, HIGH);  // panel off (P-MOS)
    pinMode(pins::EPD_BUSY, INPUT);
    pinMode(pins::EPD_CS, OUTPUT);
    pinMode(pins::EPD_DC, OUTPUT);
    pinMode(pins::EPD_RST, OUTPUT);
    spi_idle_low();
    spi->begin(pins::EPD_SCK, -1, pins::EPD_MOSI, -1);
}

bool power_on() {
    last_fail = "";
    digitalWrite(pins::EPD_PWR_EN, LOW);
    delay(20);
    spi->begin(pins::EPD_SCK, -1, pins::EPD_MOSI, -1);
    spi->beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE0));
    hw_reset();
    init_otp();
    cmd(0x04);  // power on
    return wait_busy_cycle(5000, "power_on");
}

bool power_off() {
    cmd(0x02);  // power off
    data(0x00);
    bool ok = wait_busy_cycle(5000, "power_off");
    cmd(0x07);  // deep sleep
    data(0xA5);
    delay(10);
    spi->endTransaction();
    digitalWrite(pins::EPD_PWR_EN, HIGH);
    delay(5);
    spi_idle_low();
    return ok;
}

bool refresh_solid(Color color) {
    last_fail = "";
    if (!power_on()) {
        power_off();
        return false;
    }
    uint8_t packed = 0;
    uint8_t two = static_cast<uint8_t>(color) & 0x03;
    packed = (two << 6) | (two << 4) | (two << 2) | two;

    cmd(0x10);
    dc(HIGH);
    cs(LOW);
    for (int i = 0; i < FRAME_BYTES; i++) {
        send_byte(packed);
    }
    cs(HIGH);

    const uint8_t drf[] = {0x00};
    cmd_data(0x12, drf, sizeof(drf));
    bool ok = wait_busy_cycle(30000, "refresh");
    bool off_ok = power_off();
    return ok && off_ok;
}

}  // namespace epd
